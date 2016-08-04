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
        parser = argparse.ArgumentParser(description='TODO description')

        parser.add_argument('-n', '--case-number', default=None,
            help='The case number to use., usually of the form "cr-16-053018-2d2d"'
        )
        parser.add_argument('-e','--examiner-cidr-range', default='0.0.0.0/0',
            help='The IP/CIDR for the examiner and/or the tool. This will be added as the \
                only allowed range in the isolated security group.'
        )
        parser.add_argument('-c', '--create-workstation', action='store_true',
            help='Create a cloudresponse workstation.'
        )
        parser.add_argument('-k', '--key-name', default=None,
            help='Optional. The name of the key to use when creating the workstation. If ommited, a new key is generated.'
        )
        parser.add_argument('-b', '--bucket-id', default=None,
            help='Optional. The id of the s3 bucket to use. This must already exist'
        )



        subparsers = parser.add_subparsers()

        host_compromise_parser = subparsers.add_parser(
            'host_compromise', help=''
        )

        host_compromise_parser.add_argument('ip', help='')
        host_compromise_parser.add_argument(
            'user',
            help='this is the privileged ssh user for acquiring memory from the instance.'
        )
        host_compromise_parser.add_argument(
            'ssh_key_file',
            help='provide the path to the ssh private key for the user.'
        )
        host_compromise_parser.set_defaults(func="host_compromise")

        key_compromise_parser = subparsers.add_parser('key_compromise', help='')
        key_compromise_parser.add_argument(
            'compromised_access_key_id', help=''
        )

        key_compromise_parser.add_argument(
            'region', help='Choose a region to store your case logs.  Example: us-east-1'
        )

        key_compromise_parser.set_defaults(func="key_compromise")

        create_workstation_parser = subparsers.add_parser(
            'create_workstation', help='Create an analysis workstartion'
        )

        create_workstation_parser.add_argument(
            'region', help='Choose a launch region.  Example: create_workstation us-west-2'
        )

        create_workstation_parser.set_defaults(func="create_workstation")

        args = parser.parse_args()

        try:
            func = args.func
        except AttributeError:
            parser.print_usage()
            print("no subcommand specified")
            return nullCli()

        if args.func == 'create_workstation' and args.case_number is None:
            parser.print_help()
            return nullCli()
            raise ValueError('create_workstation requires a --case-number be provided')

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

        if self.config.func == 'create_workstation' or self.config.create_workstation:
            workstation = aws_ir.CreateWorkstation(
                self.config.examiner_cidr_range,
                key_name=self.config.key_name,
                case_number=case_number,
                region=self.config.region
            )
            workstation.create()

    def test_stop_instance(self, test):
        located = test.locate_instance(self.config.ip)
        response = test.stop_instance(located['instance_id'], located['region'])
        pprint.pprint(response)

    def test_disable_access_key(self, test):
        test.disable_access_key('us-east-1', self.config.compromised_access_key_id)

    def test_snapshot_volumes(self, test):
        vids = test.inventory[0]['volume_ids']
        region = test.inventory[0]['region']
        print(test.snapshot_volumes(vids, region))


if __name__=='__main__':
   c = cli()
   if c.prog is not None:
       c.run()
