import copy
import pytest

from aws_ir.cli import cli


@pytest.fixture
def cli_object():
    cli_object = cli()
    return cli_object


def test_parse_args():
    cli = cli_object()
    case_number = "cr-17-000001-2d2d"
    cidr_range = "0.0.0.0/0"
    bucket_name = "crn-00001-assets"
    profile = "default"

    optional_args = ["--profile", profile,
                     "--case-number", case_number,
                     "--examiner-cidr-range", cidr_range,
                     "--bucket-name", bucket_name, "--dry-run"]
    instance_ip = "172.16.20.1"
    user = "ec2-user"
    ssh_key = "ssh.key"
    instance_compromise_args = [
        "instance-compromise",
        "--target",
        instance_ip,
        "--user",
        user,
        "--ssh-key",
        ssh_key
    ]
    access_key_id = "AKIAIOSFODNN7EXAMPLE"
    key_compromise_args = ["key-compromise", "--access-key-id",
                           access_key_id]

    instance_args = copy.copy(optional_args)
    key_args = copy.copy(optional_args)

    instance_args.extend(instance_compromise_args)
    parsed_instance_args = cli.parse_args(instance_args)

    key_args.extend(key_compromise_args)
    parsed_key_args = cli.parse_args(key_args)

    # Check instance-compromise arguments
    assert parsed_instance_args.case_number == case_number
    assert parsed_instance_args.examiner_cidr_range == cidr_range
    assert parsed_instance_args.bucket_name == bucket_name
    assert parsed_instance_args.dry_run is True
    # Check instance-compromise required arguments
    assert parsed_instance_args.target == instance_ip
    assert parsed_instance_args.user == user
    assert parsed_instance_args.ssh_key == ssh_key
    # Check Key Compromise required arguments are not present
    with pytest.raises(AttributeError):
        assert parsed_instance_args.access_key_id == access_key_id
    # Check that the correct fuction has been selected
    assert parsed_instance_args.func == "instance_compromise"

    # Check key compromise optional arguments
    assert parsed_key_args.case_number == case_number
    assert parsed_key_args.examiner_cidr_range == cidr_range
    assert parsed_key_args.bucket_name == bucket_name
    assert parsed_key_args.dry_run is True
    # Check key compromise required arguments
    assert parsed_key_args.access_key_id == access_key_id
    # Check Instance Compromise required arguments are not present
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
