#!/usr/bin/env python
import sys
import argparse
import logging

import aws_ir
from aws_ir import __version__
from aws_ir.libs import case

#Support for multiple incident plans coming soon
from aws_ir.plans import key
from aws_ir.plans import host

"""Basic arg parser for AWS_IR cli"""
class cli():
    def __init__(self):
        self.config = None
        self.prog = sys.argv[0].split('/')[-1]


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
            '--version',
            action='version',
            version="%(prog)s {ver}".format(ver=__version__))

        optional_args.add_argument(
            '--verbose',
            action='store_true',
            help='log debug messages')

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

        instance_compromise_parser = subparsers.add_parser(
            'instance-compromise', help=''
        )

        instance_compromise_parser.add_argument(
            '--instance-ip',
            required=True,
            help='')
        instance_compromise_parser.add_argument(
            '--user',
            required=True,
            help="""
                this is the privileged ssh user
                for acquiring memory from the instance.
            """
        )
        instance_compromise_parser.add_argument(
            '--ssh-key',
            required=True,
            help='provide the path to the ssh private key for the user.'
        )
        instance_compromise_parser.set_defaults(func="instance_compromise")

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

        case_obj = case.Case(
            self.config.case_number,
            self.config.examiner_cidr_range,
            self.config.bucket_name
        )

        if self.config.verbose:
            log_level = logging.DEBUG;
        else:
            log_level = logging.INFO

        aws_ir.set_stream_logger(level=log_level)
        aws_ir.set_file_logger(case_obj.case_number, level=log_level)
        logger = logging.getLogger(__name__)

        aws_ir.wrap_log_file(case_obj.case_number)
        logger.info("Initialization successful proceeding to incident plan.")
        compromise_object = None
        if self.config.func == 'instance_compromise':
            hc = host.Compromise(
                user = self.config.user,
                ssh_key_file = self.config.ssh_key,
                compromised_host_ip = self.config.instance_ip,
                prog = self.prog,
                case = case_obj
            )
            compromise_object = hc
            try:
                hc.mitigate()
            except KeyboardInterrupt:
                pass
        elif self.config.func == 'key_compromise':
            kc = key.Compromise(
                self.config.examiner_cidr_range,
                self.config.access_key_id,
                case = case_obj
            )

            compromise_object = kc
            try:
                kc.mitigate()
            except KeyboardInterrupt:
                pass


if __name__=='__main__':
   c = cli()
   if c.prog is not None:
       c.run()
