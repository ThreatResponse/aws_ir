#!/usr/bin/env python
import datetime
import pprint
import sys
import argparse
import logging
import json

import aws_ir

class nullCli():
    def __init__(self):
        self.config = None
        self.prog = None

class cli():

    def __init__(self):
        self.config, self.prog = self.parse_args()

    def module_missing(self, module_name):
        try:
            __import__(module_name)
        except ImportError as e:
            return True
        else:
            return False

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="""
                Incident Response command line for Amazon Web Services.
                This command line interface is designed to process host and key
                based incursions without delay or error.
            """
        )

        parser.add_argument(
            '-n',
            '--case-number',
            default=None,
            help="""
                The case number to use., usually of the form "cr-16-053018-2d2d"
            """
        )

        parser.add_argument(
            '-e',
            '--examiner-cidr-range',
            default='0.0.0.0/0',
            help="""
                The IP/CIDR for the examiner and/or the tool.
                This will be added as the only allowed range
                in the isolated security group.
            """
        )

        parser.add_argument(
            '-b',
            '--bucket-id',
            default=None,
            help="""
                Optional.
                The id of the s3 bucket to use.
                This must already exist
            """
        )

        subparsers = parser.add_subparsers()

        host_compromise_parser = subparsers.add_parser(
            'host_compromise', help=''
        )

        host_compromise_parser.add_argument('ip', help='')
        host_compromise_parser.add_argument(
            'user',
            help="""
                this is the privileged ssh user
                for acquiring memory from the instance.
            """
        )
        host_compromise_parser.add_argument(
            'ssh_key_file',
            help='provide the path to the ssh private key for the user.'
        )
        host_compromise_parser.set_defaults(func="host_compromise")

        key_compromise_parser = subparsers.add_parser(
            'key_compromise',
            help=''
        )

        key_compromise_parser.add_argument(
            'compromised_access_key_id', help=''
        )

        key_compromise_parser.add_argument(
            'region',
            help='Choose a region to store your case logs.  Example: us-east-1'
        )

        key_compromise_parser.set_defaults(func="key_compromise")

        args = parser.parse_args()

        try:
            func = args.func
        except AttributeError:
            parser.print_usage()
            print("no subcommand specified")
            return nullCli()

        if parser.prog == 'cli.py':
            prog = './'+parser.prog
        else:
            prog = parser.prog

        return args, prog

    def run(self):
        case_number = self.config.case_number
        bucket = self.config.bucket_id
        compromise_object = None
        if self.config.func == 'host_compromise':
            hc = aws_ir.HostCompromise(
                self.config.user,
                self.config.ssh_key_file,
                self.config.examiner_cidr_range,
                self.config.ip,
                case_number = self.config.case_number,
                bucket = self.config.bucket_id,
                prog = self.prog
            )
            case_number = hc.case_number
            compromise_object = hc
            try:
                hc.mitigate()
            except KeyboardInterrupt:
                pass
        elif self.config.func == 'key_compromise':
            kc = aws_ir.KeyCompromise(
                self.config.examiner_cidr_range,
                self.config.compromised_access_key_id,
                case_number = self.config.case_number,
                bucket = self.config.bucket_id,
                region = self.config.region
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
