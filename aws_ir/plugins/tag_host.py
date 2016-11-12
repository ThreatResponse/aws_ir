import uuid
import boto3

class Tag(object):
    def __init__(
        self,
        client,
        compromised_resource,
        dry_run
    ):
        self.client = client
        self.compromised_resource = compromised_resource
        self.compromise_type = compromised_resource['compromise_type']
        self.dry_run = dry_run
        self.security_group = self.setup()

    def setup(self):
        self.__add_incident_tag_to_instance()
        return True

    def __create_tags(self):
        tag = [
            {
                'Key': 'cr-case-number',
                'Value': self.compromised_resource['case_number']
            }
        ]

        return tag

    def __add_incident_tag_to_instance(self):
        region = self.compromised_resource['region']
        instance_id = self.compromised_resource['instance_id']
        try:
            self.client.create_tags(
                DryRun=self.dry_run,
                Resources=[instance_id],
                Tags=self.__create_tags()
            )
        except Exception as e:
            if e.response['Error']['Message'] == """
            Request would have succeeded, but DryRun flag is set.
            """:
                return None
            else:
                return e
