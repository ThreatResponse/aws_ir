import base64
import boto3

from jinja2 import template

class RevokeSTS(object):
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

            self.setup()

    def setup(self):
        pass

    def __locate_access_key(self):
        pass

    def __generate_inline_policy(self):
        pass

    def __attach_inline_policy(self):
        pass
