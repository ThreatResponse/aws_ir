#!/usr/bin/env python
import pytest
import argparse
import mock
import moto
from aws_ir import cloudtrail

def setup():

    pass

def test_cloudtrail_client():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    assert ct.client is not None

def test_trail_list():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    assert ct.has_trails is True

def test_ct_client():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    client = ct.get_client()
    assert client is not None

def test_invalid_ct_region():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    client = ct.get_client('pastramisandwich')
    assert client is not None

def test_get_aws_cloudtrails():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    response = ct.get_aws_cloudtrails
    assert response is not None

def test_has_trails_true():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    ct.trail_list = {u'trailList': [{u'IncludeGlobalServiceEvents': True, u'Name': u'krug-uswest-1-cloudtrail', u'TrailARN': u'arn:aws:cloudtrail:us-west-2:671642278147:trail/krug-uswest-1-cloudtrail', u'LogFileValidationEnabled': False, u'IsMultiRegionTrail': False, u'S3BucketName': u'krug-uswest-1-cloudtrail', u'HomeRegion': u'us-west-2'}], 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': '89f955cf-3afb-11e6-963d-9b7db611715f'}}
    assert ct.has_trails is True

def test_has_trails_false():
    ct = cloudtrail.CloudTrail(['us-west-2', 'us-east-1'])
    ct.trail_list = {u'trailList': []}
    assert ct.has_trails is False

def test_null_trail():
    ct = cloudtrail.nullCloudTrail()
    assert ct.client is None
    assert ct.regions is None
    assert ct.trail_list is None
