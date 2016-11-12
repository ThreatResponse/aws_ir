#!/usr/bin/env python
from datetime import datetime, timedelta
import pprint
import boto3
import logging
import os
import random
import requests
import subprocess
import sys
import tempfile
import time
import json

from libs import ts_logger
from libs import connection
from libs import aws
from libs import s3bucket
from libs import inventory
from libs import cloudtrail
from libs import compromised
from libs import volatile

from plugins import isolate_host
from plugins import tag_host
from plugins import gather_host
from plugins import snapshotdisks_host
from plugins import stop_host
from plugins import disableaccess_key

class MissingDependencyError(RuntimeError):
    """ Thrown when this program is missing a dependency. """
    pass

class AWS_IR(object):
    case_type = ''
    def __init__(self, examiner_cidr_range='0.0.0.0/0', case_number=None, bucket=None):
        self.create_time = datetime.utcnow()
        self.case_number = case_number
        self.logger = logging.getLogger('aws_ir.cli')
        streamhandler = logging.StreamHandler(sys.stdout)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        streamhandler.setFormatter(formatter)
        self.logger.addHandler(streamhandler)

        self.inventory = []
        self.examiner_cidr_range = examiner_cidr_range

        self.session = boto3.Session()
        self.json_entries = []
        self.bucket = None

    @property
    def case_number(self):
        return self._case_number

    @case_number.setter
    def case_number(self, case_number):
        if case_number is None:
            self._case_number = datetime.utcnow().strftime(
                'cr-%y-%m%d%H-{0:04x}'
                ).format(
                    random.randint(0,2**16)
            )
        else:
            self._case_number = case_number

    def event_to_logs(self, message):
        json_event = ts_logger.timesketch_logger(message, self.case_number)
        self.logger.info(message)

    def setup_bucket(self, region):
        if self.bucket == None:
            self.bucket = s3bucket.CaseBucket(self.case_number, region).bucket.name
            self.event_to_logs("Setup bucket {bucket} found.".format(
                    bucket=self.bucket
                )
            )

    def rename_log_file(self, case_number, resource_id):
        os.rename(
            ("/tmp/{case_number}-aws_ir.log").format(
                case_number=case_number,
                ),
            ("/tmp/{case_number}-{resource_id}-aws_ir.log").format(
                case_number=case_number,
                resource_id=resource_id
                )
        )

    def get_case_logs(self):
        files = []
        for file in os.listdir("/tmp"):
            if file.startswith(self.case_number):
                files.append(file)
        return files

    def copy_logs_to_s3(self):
        s3 = boto3.resource('s3')
        case_bucket = s3.Bucket(self.bucket)
        logs = self.get_case_logs()
        for log in logs:
            case_bucket.upload_file(str("/tmp/" + log), log)

    def mitigate(self):
        raise NotImplementedError('Use HostCompromise or KeyCompromise')

    def setup(self):
        """ Get all the required information before doing the mitigation. """
        client = connection.Connection(
            type='client',
            service='ec2'
        ).connect()

        self.event_to_logs("Initial connection to AmazonWebServices made.")
        self.amazon = aws.AmazonWebServices(
            connection.Connection(
                type='client',
                service='ec2'
            )
        )

        self.available_regions = self.amazon.regions

        self.event_to_logs("Inventory AWS Regions Complete {region_count} found.".format(
                region_count = len(self.amazon.regions)
            )
        )

        self.availability_zones = self.amazon.availability_zones

        self.event_to_logs(
                "Inventory Availability Zones Complete {zone_count} found.".format(
                zone_count = len(self.amazon.availability_zones)
            )
        )

        self.event_to_logs(
                "Beginning inventory of resources world wide.  This might take a minute..."
        )

        self.aws_inventory = inventory.Inventory(
            connection.Connection(
                type='client',
                service='ec2'
            ),
            self.available_regions
        )

        self.event_to_logs(
                "Inventory complete.  Proceeding to resource identification."
        )

        self.inventory = self.aws_inventory.inventory

        self.trail_logs = cloudtrail.CloudTrail(
            regions = self.amazon.regions,
            client = connection.Connection(
                    type='client',
                    service='cloudtrail'
                )
            ).trail_list

    def teardown(self, region, resource_id):
        """ Any final post mitigation steps """
        #Rename log file to include instance or key_id
        try:
            self.rename_log_file(self.case_number, resource_id)
        except:
            pass
        self.copy_logs_to_s3()
        processing_end_messaging = (
            """Processing complete for {case_number}"""
        ).format(case_number=self.case_number, caller="aws_ir", region=region)
        print(processing_end_messaging)

class HostCompromise(AWS_IR):
    """ Procedures for responding to a HostCompromise.
        ** For now, assume only Linux system.
    """
    case_type = 'Host'
    def __init__(self,
            user, ssh_key_file,
            examiner_cidr_range='0.0.0.0/0',
            compromised_host_ip=None,
            case_number=None,
            bucket=None,
            prog=None
        ):
        if compromised_host_ip==None:
            raise ValueError('Must specifiy an IP for the compromised host')
        if not os.path.exists(ssh_key_file):
            raise ValueError('Key file must exist. Could not find path {0}'.format(ssh_key_file))

        self.prog = prog
        self.ssh_key_file_path = ssh_key_file
        self.user = user


        self.compromised_host_ip = compromised_host_ip
        super(HostCompromise, self).__init__(examiner_cidr_range, case_number=case_number, bucket=bucket)

    def mitigate(self):
        self.setup()

        search = self.aws_inventory.locate_instance(self.compromised_host_ip)

        if search == None:
            raise ValueError('Compromised IP Address not found in inventory.')

        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory = search,
            case_number=self.case_number,
            type_of_compromise='host_compromise'
        ).data()

        client = connection.Connection(
            type='client',
            service='ec2',
            region=compromised_resource['region']
        ).connect()


        self.setup_bucket(compromised_resource['region'])


        # step 1 - isolate
        isolate_host.Isolate(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        # step 2 - apply compromised tag
        tag_host.Tag(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        #step 3 - get instance metadata and store it
        gather_host.Gather(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )


        # step 4 - create snapshot
        snapshotdisks_host.Snapshotdisks(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        # step 5 - gather memory
        if compromised_resource['platform'] == 'windows':
            self.event_to_logs('Platform is Windows skipping live memory')
        else:
            self.event_to_logs(
                "Attempting run margarita shotgun for {user} on {ip} with {keyfile}".format(
                    user=self.user,
                    ip=self.compromised_host_ip,
                    keyfile=self.ssh_key_file_path
                    )
                )
            try:
                volatile_data = volatile.Memory(
                    client=client,
                    compromised_resource = compromised_resource,
                    dry_run=False
                )

                results = volatile_data.get_memory(
                      bucket=self.bucket,
                      ip=self.compromised_host_ip,
                      user=self.user,
                      key=self.ssh_key_file_path,
                      case_number=self.case_number
                 )

                self.event_to_logs(("memory capture completed for: {0}, "
                                    "failed for: {1}".format(results['completed'],
                                                             results['failed'])))
            except Exception as ex:
                # raise keyboard interrupt passed during memory capture
                if isinstance(ex, KeyboardInterrupt):
                    raise
                else:
                    self.event_to_logs(
                        (
                            "Memory acquisition failure with exception"
                              "{exception}. ".format(
                                                exception=ex
                            )
                        )
                    )


        # step 6 - shutdown instance
        stop_host.Stop(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        self.teardown(
            region=self.compromised_resource['region'],
            resource_id=self.compromised_resource['instance_id']
        )

class KeyCompromise(AWS_IR):
    case_type = 'Key'
    def __init__(self,
            examiner_cidr_range='0.0.0.0/0',
            compromised_access_key_id=None,
            case_number=None,
            bucket=None,
            region=None
        ):
        if compromised_access_key_id==None:
            raise ValueError('Must specifiy an access_key_id for the compromised key.')
        self.compromised_access_key_id = compromised_access_key_id
        self.region = region
        super(KeyCompromise, self).__init__(
            examiner_cidr_range,
            case_number=case_number,
            bucket=bucket
        )

    def mitigate(self):
        self.setup()
        self.setup_bucket(region=self.region)

        access_key = self.compromised_access_key_id
        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory = {
                'access_key_id': access_key,
                'region': self.region
            },
            case_number=self.case_number,
            type_of_compromise='key_compromise'
        ).data()

        client = connection.Connection(
            type='client',
            service='ec2',
            region=compromised_resource['region']
        ).connect()

        self.event_to_logs(
                "Attempting key disable."
        )
        # step 1 - disable access key
        disableaccess_key.Disableaccess(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        self.event_to_logs(
                "Disable complete.  Uploading results."
        )

        self.teardown(
            region=self.region,
            resource_id=self.compromised_access_key_id
        )
