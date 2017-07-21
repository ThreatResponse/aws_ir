#!/usr/bin/env python
import argparse
import logging
import os
import sys


import aws_ir
from aws_ir import __version__
from aws_ir.libs import case
from aws_ir.libs import plugin

# Support for multiple incident plans coming soon
from aws_ir.plans import host
from aws_ir.plans import key


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
            '--profile',
            default='default',
            help="""
                A named boto profile to use instead of the default profile.
                """
        )

        optional_args.add_argument(
            '--case-number',
            default=None,
            help="""
                The case number to use., usually of the form
                "cr-16-053018-2d2d"
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
            '--target',
            required=False,
            help="""
                instance-id|instance-ip
            """
        )

        instance_compromise_parser.add_argument(
            '--targets',
            required=False,
            help="""
                File of resources to process instance-id or ip-address.
            """
        )

        instance_compromise_parser.add_argument(
            '--user',
            required=False,
            help="""
                this is the privileged ssh user
                for acquiring memory from the instance.
                Required for memory only.
            """
        )
        instance_compromise_parser.add_argument(
            '--ssh-key',
            required=False,
            help='provide the path to the ssh private key for the user. Required for memory only.'
        )

        instance_compromise_parser.add_argument(
            '--plugins',
            required=False,
            default="gather_host,isolate_host,"
                    "tag_host,snapshotdisks_host,"
                    "examineracl_host,get_memory,stop_host",
            help="Run some or all of the plugins in a custom order. "
                 "Provided as a comma separated list of "
                 "supported plugins: \n"
                 "{p}".format(
                    p=plugin.Core().instance_plugins()
                 )
        )

        instance_compromise_parser.set_defaults(func="instance_compromise")

        key_compromise_parser = subparsers.add_parser(
            'key-compromise',
            help=''
        )

        key_compromise_parser.add_argument(
            '--access-key-id', required=True, help=''
        )

        key_compromise_parser.add_argument(
            '--plugins',
            default="disableaccess_key,revokests_key",
            required=False,
            help="Run some or all of the plugins in a custom order."
                 " Provided as a comma separated list"
                 "Supported plugins: \n"
                 "{p}".format(
                    p=plugin.Core().key_plugins()
                 )
        )

        key_compromise_parser.set_defaults(func="key_compromise")

        return parser.parse_args(args)

    """Logic to decide on host or key compromise"""
    def run(self):
        self.config = self.parse_args(sys.argv[1:])
        case_obj = case.Case(
            self.config.case_number,
            self.config.examiner_cidr_range,
            self.config.bucket_name,
            self.config.profile
        )

        if self.config.verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        aws_ir.set_stream_logger(level=log_level)
        aws_ir.set_file_logger(case_obj.case_number, level=log_level)
        logger = logging.getLogger(__name__)

        aws_ir.wrap_log_file(case_obj.case_number)
        logger.info("Initialization successful proceeding to incident plan.")
        if self.config.func == 'instance_compromise':
            if self.config.target:
                case_obj.prep_aws_connections()
                hc = host.Compromise(
                    user=self.config.user,
                    ssh_key_file=self.config.ssh_key,
                    target=self.config.target,
                    prog=self.prog,
                    case=case_obj,
                    steps=self.config.plugins
                )
                try:
                    hc.mitigate()
                except KeyboardInterrupt:
                    pass
            if self.config.targets:
                logger.info(
                    'Alert : multi-host mode engaged targets in file will attempt processing.'
                )
                batch_file = os.path.abspath(self.config.targets)

                with open(batch_file) as f:
                    targets = f.read().split('\n')

                for target in targets:
                    if target is not '':
                        hc = host.Compromise(
                            user=self.config.user,
                            ssh_key_file=self.config.ssh_key,
                            target=target,
                            prog=self.prog,
                            case=case_obj,
                            steps=self.config.plugins
                        )
                        try:
                            logger.info("Attempting processing instance {i}".format(i=target))
                            hc.mitigate()
                        except KeyboardInterrupt:
                            pass
        elif self.config.func == 'key_compromise':
            kc = key.Compromise(
                examiner_cidr_range=self.config.examiner_cidr_range,
                compromised_access_key_id=self.config.access_key_id,
                region='us-west-2',
                case=case_obj,
                steps=self.config.plugins
            )

            try:
                kc.mitigate()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    c = cli()
    if c.prog is not None:
        c.run()
