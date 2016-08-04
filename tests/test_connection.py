#!/usr/bin/env python
import pytest
import argparse
import mock
import moto
from aws_ir import connection

def setup():

    pass

@moto.mock_ec2
def test_object_initialization():
    c = connection.Connection()
    assert c is not None
    assert c.region is  None
    assert c.connection_type is None
    assert c.service is  None
    assert c.client is  None
    assert c.resource is  None

@moto.mock_ec2
def test_connection_type():
    c = connection.Connection()
    c.connection_type = "client"
    assert c.connection_type == "client"

@moto.mock_ec2
def test_none_connection():
    c = connection.Connection()
    c.connection_type = None
    with pytest.raises(StandardError):
        assert c.connect()


@moto.mock_ec2
def test_failing_connection_type():
    c = connection.Connection()
    c.connection_type = 'potatosalad'
    with pytest.raises(StandardError):
        assert c.connect()


@moto.mock_ec2
def test_aws_lowlevel_client():
    c = connection.Connection()
    c.connection_type = "client"
    c.service = "ec2"
    c.region = "us-west-2"
    c.connect()
    assert c.resource is None
    assert c.client is not None

@moto.mock_ec2
def test_aws_resource_client():
    c = connection.Connection()
    c.connection_type = "resource"
    c.service = "ec2"
    c.region = "us-west-2"
    c.connect()
    assert c.client is None
    assert c.resource is not None
