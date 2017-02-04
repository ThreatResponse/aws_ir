
"""Compromise class for Key Compromise Procedure"""
class Compromise(object):

    def __init__(self,
            examiner_cidr_range='0.0.0.0/0',
            compromised_access_key_id=None,
            case_number=None,
            bucket=None,
            region=None
        ):

        if compromised_access_key_id==None:
            raise ValueError(
                    'Must specifiy an access_key_id for the compromised key.'
            )

        self.case_type = 'Key'
        self.compromised_access_key_id = compromised_access_key_id
        self.region = region
        super(KeyCompromise, self).__init__(
            examiner_cidr_range,
            case_number=case_number,
            bucket=bucket
        )

    def mitigate(self):
        self.setup()
        self.setup_bucket(region=self.region)

        access_key = self.compromised_access_key_id
        compromised_resource = compromised.CompromisedMetadata(
            compromised_object_inventory = {
                'access_key_id': access_key,
                'region': self.region
            },
            case_number=self.case_number,
            type_of_compromise='key_compromise'
        ).data()

        client = connection.Connection(
            type='client',
            service='ec2',
            region=compromised_resource['region']
        ).connect()

        self.event_to_logs(
                "Attempting key disable."
        )


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

        self.event_to_logs(
                "STS Tokens revoked issued prior to NOW."
        )

        self.event_to_logs(
                "Disable complete.  Uploading results."
        )

        self.teardown(
            region=self.region,
            resource_id=self.compromised_access_key_id
        )
