#!/usr/bin/python

import pytest
import boto3
import base64
import os

from faker import Factory
from dotenv import Dotenv
from aws_ir.aws_ir import cli

def setup_module():
    """To-do figure out how to properly test arg parser"""
    pass

def test_command_line_exists():
    pass


def teardown_module():
    pass
