import logging

from aws_ir.libs import compromised
from aws_ir.libs import connection
from aws_ir.libs import plugin

logger = logging.getLogger(__name__)


"""Compromise class for Key Compromise Procedure"""

class Compromise(object):

    def __init__(
        self,
        examiner_cidr_range='0.0.0.0/0',
        compromised_access_key_id=None,
        region='us-west-2',
        case=None
    ):

        if compromised_access_key_id is None:
            raise ValueError(
                'Must specify an access_key_id for the compromised key.'
            )

        self.case_type = 'Key'
        self.compromised_access_key_id = compromised_access_key_id
        self.region = region
        self.case = case
        self.plugins = plugin.Core()
        self.steps = ['disableaccess_key', 'revokests_key']

    def mitigate(self):
        """Any steps that run as part of key compromises."""
        access_key = self.compromised_access_key_id
        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory={
                'access_key_id': access_key,
                'region': self.region
            },
            case_number=self.case.case_number,
            type_of_compromise='key_compromise'
        ).data()

        session = connection.Connection(
            type='session',
            region=compromised_resource['region']
        ).connect()

        logger.info("Attempting key disable.")

        for action in self.steps:
            step = self.plugins.source.load_plugin(action)
            step.Plugin(
                boto_session=session,
                compromised_resource=compromised_resource,
                dry_run=False
            )

        logger.info("STS Tokens revoked issued prior to NOW.")

        logger.info("Disable complete.  Uploading results.")

        self.case.teardown(
            region=self.region,
            resource_id=self.compromised_access_key_id
        )
