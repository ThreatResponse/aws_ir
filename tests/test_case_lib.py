import pytest
import boto3
import base64
import os
import sys
import copy

sys.path.append(os.getcwd()+"/aws_ir")
from ..aws_ir.libs import case


def test_object_init():
    c = case.Case(
        case_number=None,
        examiner_cidr_range='0.0.0.0/0'
    )

    l = case.Logger()

    assert c is not None
    assert l is not None


def teardown_test():
    try:
        CLIENT.delete_objects(
            Bucket=UUID,
            Delete={
                'Objects': [
                    {
                        'Key': 'TestFileName'
                    }
                ]
            }
        )

        response = CLIENT.delete_bucket(
            Bucket=UUID
        )
    except:
        pass
