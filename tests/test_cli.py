#!/usr/bin/python

import pytest
import boto3
import base64
import os
import sys
import copy

sys.path.append(os.getcwd()+"/aws_ir")
from ..aws_ir import cli


@pytest.fixture
def cli_object():
    cli_object = cli.cli()
    return cli_object

def test_parse_args():
    print(sys.path)
    #assert(False)
    cli = cli_object()
    case_number = "cr-17-000001-2d2d"
    cidr_range = "0.0.0.0/0"
    bucket_name = "crn-00001-assets"
    optional_args = ["--case-number", case_number,
                     "--examiner-cidr-range", cidr_range,
                     "--bucket-name", bucket_name, "--dry-run"]
    instance_ip = "172.16.20.1"
    user = "ec2-user"
    ssh_key = "ssh.key"
    host_compromise_args = ["host-compromise", "--instance-ip", instance_ip,
                            "--user", user, "--ssh-key", ssh_key]
    access_key_id = "AKIAIOSFODNN7EXAMPLE"
    key_compromise_args = ["key-compromise", "--access-key-id",
                           access_key_id]

    host_args = copy.copy(optional_args)
    key_args = copy.copy(optional_args)

    host_args.extend(host_compromise_args)
    parsed_host_args = cli.parse_args(host_args)

    key_args.extend(key_compromise_args)
    parsed_key_args = cli.parse_args(key_args)

    # Check Host compromise arguments
    assert parsed_host_args.case_number == case_number
    assert parsed_host_args.examiner_cidr_range == cidr_range
    assert parsed_host_args.bucket_name == bucket_name
    assert parsed_host_args.dry_run == True
    # Check Host compromise required arguments
    assert parsed_host_args.instance_ip == instance_ip
    assert parsed_host_args.user == user
    assert parsed_host_args.ssh_key == ssh_key
    # Check Key Compromise required arguments are not present
    with pytest.raises(AttributeError):
        assert parsed_host_args.access_key_id == access_key_id
    # Check that the correct fuction has been selected
    assert parsed_host_args.func == "host_compromise"

    # Check key compromise optional arguments
    assert parsed_key_args.case_number == case_number
    assert parsed_key_args.examiner_cidr_range == cidr_range
    assert parsed_key_args.bucket_name == bucket_name
    assert parsed_key_args.dry_run == True
    # Check key compromise required arguments
    assert parsed_key_args.access_key_id == access_key_id
    # Check Host Compromise require arguments are not present
    with pytest.raises(AttributeError):
        assert parsed_key_args.instance_ip == instance_ip
    with pytest.raises(AttributeError):
        assert parsed_key_args.user == user
    with pytest.raises(AttributeError):
        assert parsed_key_args.ssh_key == ssh_key
    # Check that the correct fuction has been selected
    assert parsed_key_args.func == "key_compromise"


def teardown_module():
    pass
