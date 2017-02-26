"""Case management operations for AWS_IR."""

import random
import logging
import sys
import os

from datetime import datetime, timedelta

from aws_ir.libs import ts_logger
from aws_ir.libs import s3bucket
from aws_ir.libs import connection
from aws_ir.libs import aws
from aws_ir.libs import inventory


class Case(object):
    """Takes case number and examiner cidr."""
    def __init__(
        self, case_number=None,
        examiner_cidr_range='0.0.0.0/0',
        case_bucket=None
    ):
        if case_number:
            self.case_number = case_number
        else:
            self.case_number = self.__generate_case_number()

        if case_bucket:
            self.case_bucket = case_bucket
        else:
            self.case_bucket = self.__setup_bucket(region='us-west-2')

        self.case_logger = Logger(self.case_number)
        self.examiner_cidr_range = examiner_cidr_range


    def prep_aws_connections(self):
        """ Get all the required information before doing the mitigation. """
        client = connection.Connection(
            type='client',
            service='ec2'
        ).connect()

        self.case_logger.event_to_logs("Initial connection to AmazonWebServices made.")

        self.amazon = aws.AmazonWebServices(
            connection.Connection(
                type='client',
                service='ec2'
            )
        )

        self.available_regions = self.amazon.regions

        self.case_logger.event_to_logs("Inventory AWS Regions Complete {region_count} found.".format(
                region_count = len(self.amazon.regions)
            )
        )

        self.availability_zones = self.amazon.availability_zones

        self.case_logger.event_to_logs(
                "Inventory Availability Zones Complete {zone_count} found.".format(
                zone_count = len(self.amazon.availability_zones)
            )
        )

        self.case_logger.event_to_logs(
                "Beginning inventory of resources world wide.  This might take a minute..."
        )

        self.aws_inventory = inventory.Inventory(
            connection.Connection(
                type='client',
                service='ec2'
            ),
            self.available_regions
        )

        self.case_logger.event_to_logs(
                "Inventory complete.  Proceeding to resource identification."
        )

        self.inventory = self.aws_inventory.inventory


    def __rename_log_file(self, case_number, resource_id):
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

    def copy_logs_to_s3(self):
        """Convinience function to put all case logs to s3 at the end"""
        case_bucket = self.__get_case_bucket()
        logs = self.get_case_logs()
        for log in logs:
            case_bucket.upload_file(str("/tmp/" + log), log)

    def teardown(self, region, resource_id):
        """ Any final post mitigation steps universal to all plans. """
        try:
            self.__rename_log_file(self.case_number, resource_id)
            self.copy_logs_to_s3()
            processing_end_messaging = (
                """Processing complete for {case_number}"""
            ).format(case_number=self.case_number)
            print(processing_end_messaging)
            sys.exit(0)
        except Exception as e:
            sys.exit(0)
            raise


    def get_case_logs(self):
        """Enumerates all case logs based on case number from system /tmp"""
        files = []
        for file in os.listdir("/tmp"):
            if file.startswith(self.case_number):
                files.append(file)
        return files


    def __setup_bucket(self, region):
        """Wrap s3 find or create in object"""
        bucket_name = s3bucket.CaseBucket(
                self.case_number,
                region
        ).bucket.name

        return bucket_name


    def __get_case_bucket(self):
        client = connection.Connection(
            type='resource',
            service='s3'
        ).connect()
        return client.Bucket(self.case_bucket)


    def __generate_case_number(self):
        return datetime.utcnow().strftime(
            'cr-%y-%m%d%H-{0:04x}'
            ).format(
                random.randint(0,2**16)
        )

class Logger(object):
    """Case logger class for wrapping output formatters."""
    def __init__(self, case_number=None, add_handler=False, verbose=False):
        """Setup the stream logger for the object"""
        self.case_number = case_number
        self.logger = logging.getLogger('aws_ir.cli')
        self.verbose = verbose
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        streamhandler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if add_handler == True:
            streamhandler.setFormatter(formatter)
            self.logger.addHandler(streamhandler)
        else:
            pass
            #There is already a stream handler


    def event_to_logs(self, message):
        """Use timesketch logger format to create custody chain"""
        try:
            json_event = ts_logger.timesketch_logger(message, self.case_number)
            self.logger.info(message)
            return True
        except:
            return False
