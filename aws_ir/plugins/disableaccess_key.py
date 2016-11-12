import base64
import boto3

class DisableOwnKeyError(RuntimeError):
    """ Thrown when a request is made to disable the current key being used.  """
    pass

class Disableaccess(object):
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

        self.session = self.__get_boto3_session()
        self.access_key_id = self.compromised_resource['access_key_id']
        self.setup()

    def setup(self):
        if self.dry_run != True:
            self.__disable_access_key()

    def __get_boto3_session(self):
        session = boto3.Session(
            region_name='us-east-1'
        )
        return session

    def __disable_access_key(self, force_disable_self=False):
        client = self.session.client('iam')

        # we get the username for the key because even though username is optional
        # if the username is not provided, the key will not be found, contrary to what
        # the documentation says.
        response = client.get_access_key_last_used(AccessKeyId=self.access_key_id)
        username = response['UserName']

        client.update_access_key(UserName=username, AccessKeyId=self.access_key_id, Status='Inactive')
