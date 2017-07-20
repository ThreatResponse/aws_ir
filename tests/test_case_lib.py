import boto3
import os
import random
import string
import sys

from moto import mock_ec2
from moto import mock_s3

sys.path.append(os.getcwd())
from aws_ir.libs import case


class TestCaseLib(object):
    def test_object_init(self):
        # setup bucket to test providing an s3 bucket to Case class
        self.m = mock_s3()

        self.m.start()

        self.e = mock_ec2()
        self.e.start()

        self.created_buckets = []

        self.s3_resource = boto3.resource(
            service_name='s3',
            region_name='us-west-2'
        )

        self.existing_bucket_name = "case-lib-test-{0}".format(
            ''.join(
                random.choice(
                    string.ascii_lowercase + string.digits
                )
                for _ in range(10)
            )
        )

        with self.m:

            self.s3_resource.Bucket(self.existing_bucket_name).create()
            self.created_buckets.append(self.existing_bucket_name)

            # create a Case object for testing
            self.generic_case = case.Case()
            self.created_buckets.append(self.generic_case.case_bucket)

            # setup default info for log collection
            self.log_base = os.path.dirname(os.path.abspath(__file__))

            # create test files
            self.test_log = "{0}/{1}-aws_ir.log".format(
                self.log_base,
                self.generic_case.case_number
            )

            self.renamed_test_log = "{0}/{1}-{2}-aws_ir.log".format(
                self.log_base,
                self.generic_case.case_number,
                'i-12345678'
            )

            with open(self.test_log, 'w') as f:
                f.write('test log data')
                f.close()

            # create test screenshot
            self.test_jpg = "{0}/{1}-console.jpg".format(
                self.log_base,
                self.generic_case.case_number
            )

            with open(self.test_jpg, 'w') as f:
                f.write('test jpg data')
                f.close()

            # test init with no args
            case_without_args = case.Case()
            self.created_buckets.append(case_without_args.case_bucket)

            assert case_without_args is not None
            assert case_without_args.case_number is not None
            assert case_without_args.case_bucket is not None
            assert case_without_args.examiner_cidr_range == '0.0.0.0/0'

            # test init with case number
            case_with_number = case.Case(
                case_number='cr-16-022605-3da6'
            )
            self.created_buckets.append(case_with_number.case_bucket)

            assert case_with_number is not None
            assert case_with_number.case_number == 'cr-16-022605-3da6'
            assert case_with_number.case_bucket is not None
            assert case_with_number.examiner_cidr_range == '0.0.0.0/0'

            # est init with case_bucket
            case_with_bucket = case.Case(
                case_bucket=self.existing_bucket_name
            )

            assert case_with_bucket is not None
            assert case_with_bucket.case_number is not None
            assert case_with_bucket.case_bucket == self.existing_bucket_name
            assert case_with_bucket.examiner_cidr_range == '0.0.0.0/0'

            # test init with cidr_range
            case_with_cidr = case.Case(
                examiner_cidr_range='8.8.8.8/32'
            )
            self.created_buckets.append(case_with_cidr.case_bucket)

            assert case_with_cidr is not None
            assert case_with_cidr.case_number is not None
            assert case_with_cidr.case_bucket is not None
            assert case_with_cidr.examiner_cidr_range == '8.8.8.8/32'

    def test_rename_log_file(self):
        # remove this test once we can test case.teardown
        self.generic_case = case.Case()
        self.log_base = os.path.dirname(os.path.abspath(__file__))

        self.test_log = "{0}/{1}-aws_ir.log".format(self.log_base,
                                                    self.generic_case.case_number)
        self.renamed_test_log = "{0}/{1}-{2}-aws_ir.log".format(
            self.log_base,
            self.generic_case.case_number,
            'i-12345678'
        )

        with open(self.test_log, 'w') as f:
            f.write('test log data')
            f.close()

        # create test screenshot
        self.test_jpg = "{0}/{1}-console.jpg".format(
            self.log_base,
            self.generic_case.case_number
        )

        with open(self.test_jpg, 'w') as f:
            f.write('test jpg data')
            f.close()

        result = self.generic_case._Case__rename_log_file(
            self.generic_case.case_number,
            'i-12345678',
            base_dir=self.log_base
        )

        print(result)

        assert result is True

    def test_copy_logs_to_s3(self):
        # setup bucket to test providing an s3 bucket to Case class
        self.m = mock_s3()

        self.m.start()

        self.e = mock_ec2()
        self.e.start()

        self.created_buckets = []
        with self.m:
            self.s3_resource = boto3.resource(
                service_name='s3',
                region_name='us-west-2'
            )

            self.existing_bucket_name = "case-lib-test-{0}".format(
                ''.join(
                    random.choice(
                        string.ascii_lowercase + string.digits
                    )
                    for _ in range(10)
                )
            )

            self.s3_resource.Bucket(self.existing_bucket_name).create()
            self.created_buckets.append(self.existing_bucket_name)

            # create a Case object for testing
            self.generic_case = case.Case()
            self.created_buckets.append(self.generic_case.case_bucket)

            # setup default info for log collection
            self.log_base = os.path.dirname(os.path.abspath(__file__))

            # create test files
            self.test_log = "{0}/{1}-aws_ir.log".format(
                self.log_base,
                self.generic_case.case_number
            )

            self.renamed_test_log = "{0}/{1}-{2}-aws_ir.log".format(
                self.log_base,
                self.generic_case.case_number,
                'i-12345678'
            )

            with open(self.test_log, 'w') as f:
                f.write('test log data')
                f.close()

            # create test screenshot
            self.test_jpg = "{0}/{1}-console.jpg".format(
                self.log_base,
                self.generic_case.case_number
            )

            with open(self.test_jpg, 'w') as f:
                f.write('test jpg data')
                f.close()

            self.generic_case._Case__rename_log_file(
                self.generic_case.case_number,
                'i-12345678',
                base_dir=self.log_base
            )

            self.generic_case.copy_logs_to_s3(base_dir=self.log_base)

            case_bucket = self.s3_resource.Bucket(self.generic_case.case_bucket)
            uploaded_files = []
            for obj in case_bucket.objects.all():
                print(obj.key)
                uploaded_files.append(obj.key)

            test_log_key = self.renamed_test_log.split("/")[-1]
            test_jpg_key = self.test_jpg.split("/")[-1]
            assert test_log_key in uploaded_files
            assert test_jpg_key in uploaded_files
