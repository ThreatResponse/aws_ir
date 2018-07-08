import os
import shutil
import pytest
import boto3
import random
import string

from moto import mock_s3

from aws_ir.libs import case

log_base = "{}/mock_s3".format(os.path.dirname(os.path.abspath(__file__)))


def setup_module():
    if not os.path.exists(log_base):
        os.mkdir(log_base)


def teardown_module():
    shutil.rmtree(log_base, ignore_errors=True)


@pytest.fixture
def s3():
    """ is a fixture the best place for this?"""
    s3_mock = mock_s3()
    s3_mock.start()
    return s3_mock


def test_object_init(s3):
    created_buckets = []

    with s3:

        # test init with no args
        case_without_args = case.Case()
        created_buckets.append(case_without_args.case_bucket)

        assert case_without_args is not None
        assert case_without_args.case_number is not None
        assert case_without_args.case_bucket is not None
        assert case_without_args.examiner_cidr_range == '0.0.0.0/0'

        # test init with case number
        case_with_number = case.Case(
            case_number='cr-16-022605-3da6'
        )
        created_buckets.append(case_with_number.case_bucket)

        assert case_with_number is not None
        assert case_with_number.case_number == 'cr-16-022605-3da6'
        assert case_with_number.case_bucket is not None
        assert case_with_number.examiner_cidr_range == '0.0.0.0/0'

        # test init with cidr_range
        case_with_cidr = case.Case(
            examiner_cidr_range='8.8.8.8/32'
        )
        created_buckets.append(case_with_cidr.case_bucket)

        assert case_with_cidr is not None
        assert case_with_cidr.case_number is not None
        assert case_with_cidr.case_bucket is not None
        assert case_with_cidr.examiner_cidr_range == '8.8.8.8/32'


def test_init_with_existing_bucket(s3):
    created_buckets = []

    s3_resource = boto3.resource(
        service_name='s3',
        region_name='us-west-2'
    )

    existing_bucket_name = "case-lib-test-{0}".format(
        ''.join(
            random.choice(
                string.ascii_lowercase + string.digits
            )
            for _ in range(10)
        )
    )

    with s3:

        s3_resource.Bucket(existing_bucket_name).create()
        created_buckets.append(existing_bucket_name)

        case_with_bucket = case.Case(
            case_bucket=existing_bucket_name
        )

        assert case_with_bucket is not None
        assert case_with_bucket.case_number is not None
        assert case_with_bucket.case_bucket == existing_bucket_name
        assert case_with_bucket.examiner_cidr_range == '0.0.0.0/0'


def test_rename_log_file():
    # remove this test once we can test case.teardown
    generic_case = case.Case()

    test_log = "{0}/{1}-aws_ir.log".format(log_base, generic_case.case_number)

    with open(test_log, 'w') as f:
        f.write('test log data')
        f.close()

    # create test screenshot
    test_jpg = "{0}/{1}-console.jpg".format(
        log_base,
        generic_case.case_number
    )

    with open(test_jpg, 'w') as f:
        f.write('test jpg data')
        f.close()

    result = generic_case._rename_log_file(
        generic_case.case_number,
        'i-12345678',
        base_dir=log_base
    )

    assert result is True


def test_copy_logs_to_s3(s3):
    created_buckets = []
    with s3:
        s3_resource = boto3.resource(
            service_name='s3',
            region_name='us-west-2'
        )

        existing_bucket_name = "case-lib-test-{0}".format(
            ''.join(
                random.choice(
                    string.ascii_lowercase + string.digits
                )
                for _ in range(10)
            )
        )

        s3_resource.Bucket(existing_bucket_name).create()
        created_buckets.append(existing_bucket_name)

        # create a Case object for testing
        generic_case = case.Case()
        created_buckets.append(generic_case.case_bucket)

        # create test files
        test_log = "{0}/{1}-aws_ir.log".format(
            log_base,
            generic_case.case_number
        )

        renamed_test_log = "{0}/{1}-{2}-aws_ir.log".format(
            log_base,
            generic_case.case_number,
            'i-12345678'
        )

        with open(test_log, 'w') as f:
            f.write('test log data')
            f.close()

        # create test screenshot
        test_jpg = "{0}/{1}-console.jpg".format(
            log_base,
            generic_case.case_number
        )

        with open(test_jpg, 'w') as f:
            f.write('test jpg data')
            f.close()

        generic_case._rename_log_file(
            generic_case.case_number,
            'i-12345678',
            base_dir=log_base
        )

        generic_case.copy_logs_to_s3(base_dir=log_base)

        case_bucket = s3_resource.Bucket(generic_case.case_bucket)
        uploaded_files = []
        for obj in case_bucket.objects.all():
            print(obj.key)
            uploaded_files.append(obj.key)

        test_log_key = renamed_test_log.split("/")[-1]
        test_jpg_key = test_jpg.split("/")[-1]
        assert test_log_key in uploaded_files
        assert test_jpg_key in uploaded_files
