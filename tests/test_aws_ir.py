#!/usr/bin/python

import pytest
import boto3
import base64
import os
import sys

from faker import Factory

sys.path.append(os.getcwd()+"/aws_ir")
from ..aws_ir import aws_ir

CASE_NUMBER = '12345678'
EXAMINER_CIDR_RANGE = "0.0.0.0/0"
BUCKET = None

def cleanup_case_buckets():
    regions = ['us-west-2', 'us-west-1', 'us-east-1']
    for region in regions:
        s3 = boto3.client('s3', region_name=region)
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            if (bucket['Name'].split('-')[0]) == 'cloud':
                if 'cloud-response' == (
                    bucket['Name'].split('-')[0] + '-' + bucket['Name'].split('-')[1]
                    ):

                        objects = s3.list_objects(
                            Bucket=bucket['Name']
                        )


                        try:
                            """If things exist in the bucket remove them"""
                            s3.delete_objects(
                                Bucket=bucket['Name'],
                                Delete={
                                    'Objects': [
                                        objects['Contents']
                                    ]
                                }
                            )
                        except:
                            pass

                        s3.delete_bucket(
                            Bucket=bucket['Name']
                        )

                        print(bucket['Name'])
                        print("Removing bucket")
                        pass
                else:
                    pass
                    #print("Nothing to delete")


@pytest.fixture
def aws_ir_object():
    aws_ir_object = aws_ir.AWS_IR(
        examiner_cidr_range=EXAMINER_CIDR_RANGE,
        case_number=CASE_NUMBER,
        bucket=None
    )
    return aws_ir_object

def test_object_exists():
    assert aws_ir_object() is not None

def test_setup_bucket():
    a = aws_ir_object()
    a.setup_bucket(region='us-west-2')
    a.setup_bucket(region='us-east-1')
    a.setup_bucket(region='us-west-1')
    assert a.bucket is not None

def test_rename_log_file():
    a = aws_ir_object()
    res = a.rename_log_file(CASE_NUMBER, 'i-12345678-NOTREAL')
    assert res == False

def test_get_case_logs():
    a = aws_ir_object()
    res = a.get_case_logs()
    assert len(res) is not None

def test_copy_logs_to_s3():
    a = aws_ir_object()
    a.setup_bucket(region='us-west-1')
    res = a.copy_logs_to_s3()

def test_setup():
    a = aws_ir_object()
    a.setup_bucket(region='us-west-1')
    res = a.setup()
    #assert res is not None

def teardown_test():
    res = cleanup_case_buckets()
