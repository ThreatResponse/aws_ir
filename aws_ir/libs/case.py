"""Case management operations for AWS_IR."""

import random
import logging
import sys
import time
import os

from datetime import datetime, timedelta

import aws_ir
from aws_ir.libs import s3bucket
from aws_ir.libs import connection
from aws_ir.libs import aws
from aws_ir.libs import inventory

logger = logging.getLogger(__name__)


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

        self.examiner_cidr_range = examiner_cidr_range


    def prep_aws_connections(self):
        """ Get all the required information before doing the mitigation. """
        client = connection.Connection(
            type='client',
            service='ec2'
        ).connect()

        logger.info("Initial connection to AmazonWebServices made.")

        self.amazon = aws.AmazonWebServices(
            connection.Connection(
                type='client',
                service='ec2'
            )
        )

        self.available_regions = self.amazon.regions

        logger.info(("Inventory AWS Regions Complete {region_count} "
                     "found.".format(region_count = len(self.amazon.regions))))

        self.availability_zones = self.amazon.availability_zones

        logger.info(("Inventory Availability Zones Complete {zone_count} "
                     "found.".format(
                        zone_count = len(self.amazon.availability_zones)
                     )))

        logger.info(("Beginning inventory of resources world wide.  "
                     "This might take a minute..."))

        self.aws_inventory = inventory.Inventory(
            connection.Connection(
                type='client',
                service='ec2'
            ),
            self.available_regions
        )

        logger.info(("Inventory complete.  Proceeding to resource "
                     "identification."))

        self.inventory = self.aws_inventory.inventory


    def __rename_log_file(self, case_number, resource_id, base_dir="/tmp"):
        """Move all log files to standard naming format"""
        try:
            os.rename(
                ("{base_dir}/{case_number}-aws_ir.log").format(
                    base_dir=base_dir,
                    case_number=case_number,
                    ),
                ("{base_dir}/{case_number}-{resource_id}-aws_ir.log").format(
                    base_dir=base_dir,
                    case_number=case_number,
                    resource_id=resource_id
                    )
            )
            return True
        except:
            return False

    def copy_logs_to_s3(self, base_dir="/tmp"):
        """Convinience function to put all case logs to s3 at the end"""
        case_bucket = self.__get_case_bucket()
        logs = self.__get_case_logs(base_dir=base_dir)
        for log in logs:
            case_bucket.upload_file("{base_dir}/{log}".format(base_dir=base_dir,
                                                              log=log), log)

    def teardown(self, region, resource_id):
        """ Any final post mitigation steps universal to all plans. """
        try:
            aws_ir.wrap_log_file(self.case_number)
            self.__rename_log_file(self.case_number, resource_id)
            self.copy_logs_to_s3()
            processing_end_messaging = (
                """Processing complete for {case_number}\n"""
                """Artifacts stored in s3://{case_bucket}"""
            ).format(case_number=self.case_number,
                     case_bucket=self.case_bucket)
            print(processing_end_messaging)
            sys.exit(0)
        except Exception as e:
            logger.error(
                ("Error uploading case logs for {case_number} to s3 "
                 "bucket {case_bucket}: {ex}".format(case_number=self.case_number,
                                                     case_bucket=self.case_bucket,
                                                     ex=e)))
            sys.exit(1)


    def __get_case_logs(self, base_dir="/tmp"):
        """Enumerates all case logs based on case number from system /tmp"""
        files = []
        for file in os.listdir(base_dir):
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
