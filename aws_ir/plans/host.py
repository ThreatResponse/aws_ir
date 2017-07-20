import logging

from aws_ir.libs import compromised
from aws_ir.libs import connection
from aws_ir.libs import plugin
from aws_ir.libs import volatile

from aws_ir.plans import steps_to_list


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
            target=None,
            prog=None,
            case=None,
            steps=None
    ):

        if target is None:
            raise ValueError(
                'You must specify an ip-address or instance-id.'
            )

        self.prog = prog
        self.ssh_key_file_path = ssh_key_file
        self.user = user
        self.case_type = 'Host'

        self.target = target
        self.case = case

        self.plugins = plugin.Core()
        self.steps = steps_to_list(steps)

    def _target_type(self):
        """Returns the target type based on regex."""
        if len(self.target.split('.')) is 4:
            return 'ip-address'
        else:
            return 'instance-id'

    def mitigate(self):

        if self._target_type() == 'ip-address':
            search = self.case.aws_inventory.locate_instance_by_ip(
                self.target
            )
        if self._target_type() == 'instance-id':
            search = self.case.aws_inventory.locate_instance_by_id(
                self.target
            )

        if search is None:
            raise ValueError(
                'Target ip-address or instance-id not found in inventory.'
            )

        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory=search,
            case_number=self.case.case_number,
            type_of_compromise='host_compromise',
            examiner_cidr_range=self.case.examiner_cidr_range
        ).data()

        session = connection.Connection(
            type='session',
            region=compromised_resource['region']
        ).connect()

        logger.info(
            "Proceeding with incident plan steps included are {steps}".format(steps=self.steps)
        )

        for action in self.steps:
            logger.info("Executing step {step}.".format(step=action))
            if 'get_memory' not in action:
                step = self.plugins.source.load_plugin(action)
                step.Plugin(
                    boto_session=session,
                    compromised_resource=compromised_resource,
                    dry_run=False
                )
            elif 'get_memory' == action:
                logger.info("attempting memory run")
                self.do_mem(session, compromised_resource)

    def do_mem(self, session, compromised_resource):
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
                        ip=compromised_resource.get('public_ip_address', None),
                        keyfile=self.ssh_key_file_path
                    )
                )
            )

            try:
                volatile_data = volatile.Memory(
                    boto_session=session,
                    compromised_resource=compromised_resource,
                    dry_run=False
                )

                results = volatile_data.get_memory(
                    bucket=self.case.case_bucket,
                    ip=compromised_resource['public_ip_address'],
                    user=self.user,
                    key=self.ssh_key_file_path,
                    case_number=self.case.case_number
                )

                print(results)

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
