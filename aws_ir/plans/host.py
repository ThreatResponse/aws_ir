import logging
import os

from aws_ir.libs import compromised
from aws_ir.libs import connection
from aws_ir.libs import plugin
from aws_ir.libs import volatile


logger = logging.getLogger(__name__)


"""Compromise class for Host Compromise"""


class Compromise(object):
    """Procedures for responding to a HostCompromise.

    ** For now, assume only Linux system.
    """
    def __init__(
            self,
            user=None,
            ssh_key_file=None,
            compromised_host_ip=None,
            prog=None,
            case=None
    ):

        if compromised_host_ip is None:
            raise ValueError(
                'Must specifiy an IP for the compromised host'
            )

        if not os.path.exists(ssh_key_file):
            raise ValueError(
                'Key file must exist. Could not find path {0}'.format(
                    ssh_key_file
                )
            )

        self.prog = prog
        self.ssh_key_file_path = ssh_key_file
        self.user = user
        self.case_type = 'Host'

        self.compromised_host_ip = compromised_host_ip
        self.case = case

        self.plugins = plugin.Core()
        self.steps = [
            'gather_host',
            'isolate_host',
            'tag_host',
            'snapshotdisks_host',
            'examineracl_host',
            'get_memory',
            'stop_host'
        ]

    def mitigate(self):

        self.case.prep_aws_connections()

        search = self.case.aws_inventory.locate_instance(
            self.compromised_host_ip
        )

        if search is None:
            raise ValueError('Compromised IP Address not found in inventory.')

        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory=search,
            case_number=self.case.case_number,
            type_of_compromise='host_compromise',
            examiner_cidr_range=self.case.examiner_cidr_range
        ).data()

        client = connection.Connection(
            type='client',
            service='ec2',
            region=compromised_resource['region']
        ).connect()

        for action in self.steps:
            if action is not 'get_memory':
                step = self.plugins.source.load_plugin(action)
                step.Plugin(
                    client=client,
                    compromised_resource=compromised_resource,
                    dry_run=False
                )
            elif action is 'get_memory':
                self.do_mem(client, compromised_resource)

    def do_mem(self, client, compromised_resource):
        if compromised_resource['platform'] == 'windows':
            logger.info('Platform is Windows skipping live memory')
        elif self.case.examiner_cidr_range == '0.0.0.0/0':
            logger.info(
                "Examiner CIDR not provided skipping memory acquisition."
            )
        else:
            logger.info(
                (
                    "Attempting run margarita shotgun for {user} on {ip} with {keyfile}".format(
                        user=self.user,
                        ip=self.compromised_host_ip,
                        keyfile=self.ssh_key_file_path
                    )
                )
            )

            try:
                volatile_data = volatile.Memory(
                    client=client,
                    compromised_resource=compromised_resource,
                    dry_run=False
                )

                results = volatile_data.get_memory(
                    bucket=self.case.case_bucket,
                    ip=self.compromised_host_ip,
                    user=self.user,
                    key=self.ssh_key_file_path,
                    case_number=self.case.case_number
                )

                logger.info(
                    (
                        "memory capture completed for: {0}, "
                        "failed for: {1} ".format(
                            results['completed'],
                            results['failed']
                        )
                    )
                )
            except Exception as ex:
                # raise keyboard interrupt passed during memory capture
                if isinstance(ex, KeyboardInterrupt):
                    raise
                else:
                    logger.error(("Memory acquisition failure with exception "
                                  "{exception}. ".format(exception=ex)))
