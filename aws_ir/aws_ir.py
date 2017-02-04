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
from plugins import revokests_key

class MissingDependencyError(RuntimeError):
    """ Thrown when this program is missing a dependency. """
    pass

class AWS_IR(object):
    def __init__(self, examiner_cidr_range='0.0.0.0/0', case_number=None, bucket=None):
        """Setup the stream logger for the object"""
        self.logger = logging.getLogger('aws_ir.cli')
        streamhandler = logging.StreamHandler(sys.stdout)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        streamhandler.setFormatter(formatter)
        self.logger.addHandler(streamhandler)


        """Setup case specific attributes"""
        self.create_time = datetime.utcnow()
        self.case_number = case_number

        self.inventory = []
        self.examiner_cidr_range = examiner_cidr_range

        self.json_entries = []
        self.bucket = bucket



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

    def event_to_logs(self, message):
        """Use timesketch logger format to create custody chain"""
        try:
            json_event = ts_logger.timesketch_logger(message, self.case_number)
            self.logger.info(message)
            return True
        except:
            return False

    def setup_bucket(self, region):
        """Wrap s3 find or create in object"""
        if self.bucket == None:

            self.bucket = s3bucket.CaseBucket(
                    self.case_number,
                    region
            ).bucket.name

            self.event_to_logs("Setup bucket {bucket} found.".format(
                    bucket=self.bucket
                )
            )

        else:
            #Bucket is already set in constructor
            pass

    def rename_log_file(self, case_number, resource_id):
        """Move all log files to standard naming format"""
        try:
            os.rename(
                ("/tmp/{case_number}-aws_ir.log").format(
                    case_number=case_number,
                    ),
                ("/tmp/{case_number}-{resource_id}-aws_ir.log").format(
                    case_number=case_number,
                    resource_id=resource_id
                    )
            )
            return True
        except:
            return False

    def get_case_logs(self):
        """Enumerates all case logs based on case number from system /tmp"""
        files = []
        for file in os.listdir("/tmp"):
            if file.startswith(self.case_number):
                files.append(file)
        return files

    def copy_logs_to_s3(self):
        """Convinience function to put all case logs to s3 at the end"""
        s3 = boto3.resource('s3')
        case_bucket = s3.Bucket(self.bucket)
        logs = self.get_case_logs()
        for log in logs:
            case_bucket.upload_file(str("/tmp/" + log), log)

    def mitigate(self):
        """If key or host compromise is not selected raise exception"""
        raise NotImplementedError('Use HostCompromise or KeyCompromise')

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
        ).format(case_number=self.case_number)
        print(processing_end_messaging)
        sys.exit(0)
