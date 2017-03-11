import os
import logging

from aws_ir.libs import volatile
from aws_ir.libs import compromised
from aws_ir.libs import connection

from aws_ir.plugins import isolate_host
from aws_ir.plugins import tag_host
from aws_ir.plugins import gather_host
from aws_ir.plugins import snapshotdisks_host
from aws_ir.plugins import stop_host

logger = logging.getLogger(__name__)


"""Compromise class for Host Compromise"""
class Compromise(object):
    """ Procedures for responding to a HostCompromise.
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


        if compromised_host_ip==None:
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

    def mitigate(self):

        self.case.prep_aws_connections()

        search = self.case.aws_inventory.locate_instance(self.compromised_host_ip)

        if search == None:
            raise ValueError('Compromised IP Address not found in inventory.')

        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory = search,
            case_number=self.case.case_number,
            type_of_compromise='host_compromise',
            examiner_cidr_range=self.case.examiner_cidr_range
        ).data()

        client = connection.Connection(
            type='client',
            service='ec2',
            region=compromised_resource['region']
        ).connect()


        # step 1 - isolate
        isolate_host.Isolate(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        # step 2 - apply compromised tag
        tag_host.Tag(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        #step 3 - get instance metadata and store it
        gather_host.Gather(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )


        # step 4 - create snapshot
        snapshotdisks_host.Snapshotdisks(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        # step 5 - gather memory
        if compromised_resource['platform'] == 'windows':
            logger.info('Platform is Windows skipping live memory')
        else:
            logger.info(("Attempting run margarita shotgun for {user} on "
                         "{ip} with {keyfile}".format(
                             user=self.user,
                             ip=self.compromised_host_ip,
                             keyfile=self.ssh_key_file_path
                         )))
            try:
                volatile_data = volatile.Memory(
                    client=client,
                    compromised_resource = compromised_resource,
                    dry_run=False
                )

                results = volatile_data.get_memory(
                      bucket=self.case.case_bucket,
                      ip=self.compromised_host_ip,
                      user=self.user,
                      key=self.ssh_key_file_path,
                      case_number=self.case.case_number
                 )

                logger.info(("memory capture completed for: {0}, "
                                    "failed for: {1}".format(results['completed'],
                                                             results['failed'])))
            except Exception as ex:
                # raise keyboard interrupt passed during memory capture
                if isinstance(ex, KeyboardInterrupt):
                    raise
                else:
                    logger.error(("Memory acquisition failure with exception"
                                  "{exception}. ".format(exception=ex)))

        # step 6 - shutdown instance
        stop_host.Stop(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        self.case.teardown(
            region=compromised_resource['region'],
            resource_id=compromised_resource['instance_id']
        )
