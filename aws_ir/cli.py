#!/usr/bin/env python
import datetime
import pprint
import sys
import argparse
import logging
import json

#Add the AWS_IR Object
import aws_ir

#Support for multiple incident plans coming soon
from plans import key
from plans import host

"""Basic arg parser for AWS_IR cli"""
class cli():
    def __init__(self):
        self.config = None
        self.prog = sys.argv[0]

    """Throw an error on missing modules"""
    def module_missing(self, module_name):
        try:
            __import__(module_name)
        except ImportError as e:
            return True
        else:
            return False

    """Parent parser for top level flags"""
    def parse_args(self, args):

        parser = argparse.ArgumentParser(
            description="""
                Incident Response command line for Amazon Web Services.
                This command line interface is designed to process host and key
                based incursions without delay or error.
            """
        )

        optional_args = parser.add_argument_group()

        optional_args.add_argument(
            '--case-number',
            default=None,
            help="""
                The case number to use., usually of the form "cr-16-053018-2d2d"
            """
        )

        optional_args.add_argument(
            '--examiner-cidr-range',
            default='0.0.0.0/0',
            help="""
                The IP/CIDR for the examiner and/or the tool.
                This will be added as the only allowed range
                in the isolated security group.
            """
        )

        optional_args.add_argument(
            '--bucket-name',
            default=None,
            help="""
                Optional.
                The id of the s3 bucket to use.
                This must already exist
            """
        )

        optional_args.add_argument(
            '--dry-run',
            action='store_true',
            help="""
                Dry run. Pass dry run
                parameter to perform API calls
                but will not modify any resources.
            """
        )

        subparsers = parser.add_subparsers(dest="compromise-type")
        subparsers.required = True

        host_compromise_parser = subparsers.add_parser(
            'host-compromise', help=''
        )

        host_compromise_parser.add_argument(
            '--instance-ip',
            required=True,
            help='')
        host_compromise_parser.add_argument(
            '--user',
            required=True,
            help="""
                this is the privileged ssh user
                for acquiring memory from the instance.
            """
        )
        host_compromise_parser.add_argument(
            '--ssh-key',
            required=True,
            help='provide the path to the ssh private key for the user.'
        )
        host_compromise_parser.set_defaults(func="host_compromise")

        key_compromise_parser = subparsers.add_parser(
            'key-compromise',
            help=''
        )

        key_compromise_parser.add_argument(
            '--access-key-id', required=True, help=''
        )

        key_compromise_parser.set_defaults(func="key_compromise")

        return parser.parse_args(args)


    """Logic to decide on host or key compromise"""
    def run(self):
        self.config = self.parse_args(sys.argv[1:])
        case_number = self.config.case_number
        bucket = self.config.bucket_name
        compromise_object = None
        if self.config.func == 'host_compromise':
            hc = plans.key.Compromise(
                self.config.user,
                self.config.ssh_key,
                self.config.examiner_cidr_range,
                self.config.instance_ip,
                case_number = self.config.case_number,
                bucket = self.config.bucket_name,
                prog = self.prog
            )
            case_number = hc.case_number
            compromise_object = hc
            try:
                hc.mitigate()
            except KeyboardInterrupt:
                pass
        elif self.config.func == 'key_compromise':
            kc = plans.host.Compromise(
                self.config.examiner_cidr_range,
                self.config.access_key_id,
                case_number = self.config.case_number,
                bucket = self.config.bucket_name
            )
            case_number = kc.case_number
            compromise_object = kc
            try:
                kc.mitigate()
            except KeyboardInterrupt:
                pass


if __name__=='__main__':
   c = cli()
   if c.prog is not None:
       c.run()
