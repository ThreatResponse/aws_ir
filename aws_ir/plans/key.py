import logging

from aws_ir.libs import connection
from aws_ir.libs import compromised

from aws_ir.plugins import disableaccess_key
from aws_ir.plugins import revokests_key

logger = logging.getLogger(__name__)


"""Compromise class for Key Compromise Procedure"""
class Compromise(object):

    def __init__(self,
            examiner_cidr_range='0.0.0.0/0',
            compromised_access_key_id=None,
            region='us-west-2',
            case=None
        ):

        if compromised_access_key_id==None:
            raise ValueError(
                    'Must specifiy an access_key_id for the compromised key.'
            )

        self.case_type = 'Key'
        self.compromised_access_key_id = compromised_access_key_id
        self.region = region
        self.case = case


    def mitigate(self):
        """Any steps that run as part of key compromises."""
        access_key = self.compromised_access_key_id
        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory = {
                'access_key_id': access_key,
                'region': self.region
            },
            case_number=self.case.case_number,
            type_of_compromise='key_compromise'
        ).data()

        client = connection.Connection(
            type='client',
            service='iam',
            region=compromised_resource['region']
        ).connect()

        logger.info("Attempting key disable.")


        # step 1 - disable access key
        disableaccess_key.Disableaccess(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )


        # step 2 - revoke and STS tokens issued prior to now
        revokests_key.RevokeSTS(
            client=client,
            compromised_resource = compromised_resource,
            dry_run=False
        )

        logger.info("STS Tokens revoked issued prior to NOW.")

        logger.info("Disable complete.  Uploading results.")

        self.case.teardown(
            region=self.region,
            resource_id=self.compromised_access_key_id
        )
