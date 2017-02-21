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

        self.client = client #Requires an IAM Client
        self.compromised_resource = compromised_resource
        self.compromise_type = compromised_resource['compromise_type']
        self.dry_run = dry_run

        self.access_key_id = self.compromised_resource['access_key_id']
        self.setup()

    def setup(self):
        """Method runs the plugin"""
        if self.dry_run != True:
            self.__disable_access_key()

    def validate(self):
        """Returns whether this plugin does what it claims to have done"""
        client = self.client
        response = client.get_access_key_last_used(AccessKeyId=self.access_key_id)
        username = response['UserName']
        access_keys = client.list_access_keys(
            UserName=username
        )

        for key in access_keys['AccessKeyMetadata']:
            if (key['AccessKeyId'] == self.access_key_id) and (key['Status'] == 'Inactive'):
                return True

        return False

    def __disable_access_key(self, force_disable_self=False):
        """This function first checks to see if the key is already disabled\
        if not then it goes to disabling"""
        client = self.client
        #First check to see if the key is already disabled.
        if self.validate == True:
            return
        else:
            # we get the username for the key because even though username is optional
            # if the username is not provided, the key will not be found, contrary to what
            # the documentation says.
            response = client.get_access_key_last_used(AccessKeyId=self.access_key_id)
            username = response['UserName']
            client.update_access_key(
                UserName=username,
                AccessKeyId=self.access_key_id,
                Status='Inactive'
            )
