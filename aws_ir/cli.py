#!/usr/bin/env python
import sys
import argparse

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
        case_logger = case.Logger(add_handler=True, verbose=self.config.verbose)
        case_logger.event_to_logs("Parsing successful proceeding to incident plan.")
        compromise_object = None
        if self.config.func == 'host_compromise':
            hc = host.Compromise(
                user = self.config.user,
                ssh_key_file = self.config.ssh_key,
                compromised_host_ip = self.config.instance_ip,
                prog = self.prog,
                case = case.Case(
                    self.config.case_number,
                    self.config.examiner_cidr_range,
                    self.config.bucket_name

                ),
                logger = case_logger
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
                case = case.Case(
                    self.config.case_number,
                    self.config.examiner_cidr_range,
                    self.config.bucket_name

                ),
                logger = case_logger
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
