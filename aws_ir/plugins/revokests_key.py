import datetime
import boto3
import os
import fnmatch
import aws_ir

from jinja2 import Template

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
        """Method runs the plugin attaching policies to the user in question"""
        if self.dry_run == False:
            username = self.__get_username_for_key()
            policy_document = self.__generate_inline_policy()
            self.__attach_inline_policy(username, policy_document)
            pass
        pass

    def validate(self):
        """Checks the a policy is actually attached"""
        for policy in self.__get_policies()['PolicyNames']:
            if policy == "threatresponse-temporal-key-revocation":
                return True
            else:
                pass
        return False

    def __get_policies(self):
        """Returns all the policy names for a given user"""
        username = self.__get_username_for_key()
        policies = self.client.list_user_policies(
            UserName=username
        )
        return policies

    def __get_date(self):
        """Returns a date in zulu time"""
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        return now

    def __get_username_for_key(self):
        """Find the user for a given access key"""
        client = self.client
        response = client.get_access_key_last_used(
            AccessKeyId=self.compromised_resource['access_key_id']
        )
        username = response['UserName']
        return username

    def __generate_inline_policy(self):
        """Renders a policy from a jinja template"""
        template_name = self.__locate_file('deny-sts-before-time.json.j2')
        template_file = open(template_name)
        template_contents = template_file.read()
        jinja_template = Template(template_contents)
        policy_document = jinja_template.render(
            before_date=self.__get_date()
        )
        return policy_document

    def __attach_inline_policy(self, username, policy_document):
        """Attaches the policy to the user"""
        client = self.client

        response = client.put_user_policy(
            UserName=username,
            PolicyName="threatresponse-temporal-key-revocation",
            PolicyDocument=policy_document
        )
        return response

    def __locate_file(self, pattern, root=aws_ir.__path__[0]):
        '''Locate all files matching supplied filename pattern in and below
        supplied root directory.'''
        for path, dirs, files in os.walk(os.path.abspath(root)):
            for filename in fnmatch.filter(files, pattern):
                return os.path.join(path, filename)
