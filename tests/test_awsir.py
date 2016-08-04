#!/usr/bin/env python
import pytest
import argparse
import mock
import moto
from setuptools import setup
from aws_ir import cli
from aws_ir import aws_ir

def setup():

    pass

@pytest.fixture
def aws_ir_object():
    return aws_ir.AWS_IR(
        examiner_cidr_range="10.10.10.0/24",
        case_number="123456789",
        bucket="case_bucket_123456789"
    )

def test_create_time(aws_ir_object):
    assert aws_ir_object.create_time is not None

def test_case_number(aws_ir_object):
    assert aws_ir_object.case_number is "123456789"

@moto.mock_s3
@moto.mock_ec2
def test_aws_setup(aws_ir_object):
    aws_ir_object.setup()
    assert aws_ir_object.available_regions is not None

def test_init():
    pass
