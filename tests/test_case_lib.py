import pytest
import boto3
import os
import sys
import string
import random

sys.path.append(os.getcwd())
from aws_ir.libs import case


class TestCaseLib():

    @classmethod
    def setup_class(klass):
        # setup bucket to test providing an s3 bucket to Case class
        klass.created_buckets = []
        klass.s3_resource = boto3.resource('s3')
        klass.existing_bucket_name = "case-lib-test-{0}".format(
                ''.join(random.choice(string.ascii_lowercase +
                                      string.digits) for _ in range(10))
                )
        klass.s3_resource.Bucket(klass.existing_bucket_name).create()
        klass.created_buckets.append(klass.existing_bucket_name)

        # create a Case object for testing
        klass.generic_case = case.Case()
        klass.created_buckets.append(klass.generic_case.case_bucket)

        #setup default info for log collection
        klass.log_base = os.path.dirname(os.path.abspath(__file__))

        #create test files
        klass.test_log = "{0}/{1}-aws_ir.log".format(klass.log_base,
                                                     klass.generic_case.case_number)
        klass.renamed_test_log = "{0}/{1}-{2}-aws_ir.log".format(
                klass.log_base,
                klass.generic_case.case_number,
                'i-12345678'
            )

        with open(klass.test_log, 'w') as f:
            f.write('test log data')
            f.close()

        #create test screenshot
        klass.test_jpg = "{0}/{1}-console.jpg".format(klass.log_base,
                                                     klass.generic_case.case_number)
        with open(klass.test_jpg, 'w') as f:
            f.write('test jpg data')
            f.close()

    def test_object_init(self):

        #test init with no args
        case_without_args = case.Case()
        self.created_buckets.append(case_without_args.case_bucket)

        assert case_without_args is not None
        assert case_without_args.case_number is not None
        assert case_without_args.case_bucket is not None
        assert case_without_args.examiner_cidr_range == '0.0.0.0/0'

        #test init with case number
        case_with_number = case.Case(
            case_number='cr-16-022605-3da6'
        )
        self.created_buckets.append(case_with_number.case_bucket)

        assert case_with_number is not None
        assert case_with_number.case_number == 'cr-16-022605-3da6'
        assert case_with_number.case_bucket is not None
        assert case_with_number.examiner_cidr_range == '0.0.0.0/0'

        #test init with case_bucket
        case_with_bucket = case.Case(
            case_bucket=self.existing_bucket_name
        )

        assert case_with_bucket is not None
        assert case_with_bucket.case_number is not None
        assert case_with_bucket.case_bucket == self.existing_bucket_name
        assert case_with_bucket.examiner_cidr_range == '0.0.0.0/0'

        #test init with cidr_range
        case_with_cidr = case.Case(
            examiner_cidr_range='8.8.8.8/32'
        )
        self.created_buckets.append(case_with_cidr.case_bucket)

        assert case_with_cidr is not None
        assert case_with_cidr.case_number is not None
        assert case_with_cidr.case_bucket is not None
        assert case_with_cidr.examiner_cidr_range == '8.8.8.8/32'


    def test_prep_aws_connections(self):
        self.generic_case.prep_aws_connections()

        assert self.generic_case.amazon is not None
        assert self.generic_case.available_regions is not None
        assert self.generic_case.availability_zones is not None
        assert self.generic_case.aws_inventory is not None
        assert self.generic_case.inventory is not None

    def test_rename_log_file(self):
        #TODO: remove this test once we can test case.teardown
        result = self.generic_case._Case__rename_log_file(
                self.generic_case.case_number,
                'i-12345678',
                base_dir=self.log_base
            )

        assert result is True

    def test_copy_logs_to_s3(self):
        self.generic_case.copy_logs_to_s3(base_dir=self.log_base)

        uploaded_files = []
        case_bucket = self.s3_resource.Bucket(self.generic_case.case_bucket)
        for obj in case_bucket.objects.all():
            uploaded_files.append(obj.key)

        test_log_key = self.renamed_test_log.split("/")[-1]
        test_jpg_key = self.test_jpg.split("/")[-1]
        assert test_log_key in uploaded_files
        assert test_jpg_key in uploaded_files

    @classmethod
    def teardown_class(klass):
        for bucket_name in klass.created_buckets:
            #cleanup all objects in created buckets
            try:
                bucket = klass.s3_resource.Bucket(bucket_name)
                for obj in bucket.objects.all():
                    obj.delete()
                for ver_obj in bucket.object_versions.all():
                    ver_obj.delete()

                #cleanup bucket
                print("deleting bucket: {0}".format(bucket_name))
                bucket.delete()
            except:
                pass

        #cleanup files
        if os.path.isfile(klass.test_log):
            os.remove(klass.test_log)
        if os.path.isfile(klass.renamed_test_log):
            os.remove(klass.renamed_test_log)
        if os.path.isfile(klass.test_jpg):
            os.remove(klass.test_jpg)
