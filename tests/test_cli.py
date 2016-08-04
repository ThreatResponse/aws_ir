#!/usr/bin/env python
import pytest
import argparse
import mock
from setuptools import setup
from aws_ir import cli
from aws_ir import aws_ir

def setup():
    #cli.cli()
    pass

def test_null_object():
    nullCliObject = cli.nullCli()
    assert nullCliObject.prog is None
    pass
