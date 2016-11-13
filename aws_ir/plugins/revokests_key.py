import datetime
import boto3
import os

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
            self.session = self.__get_boto3_session()

            self.setup()

    def setup(self):
        if self.dry_run == False:
            username = self.__get_username_for_key()
            policy_document = self.__generate_inline_policy()
            self.__attach_inline_policy(username, policy_document)
            pass
        pass

    def __get_date(self):
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        return now

    def __get_boto3_session(self):
        session = boto3.Session(
            region_name='us-east-1'
        )
        return session

    def __get_username_for_key(self):
        client = self.session.client('iam')
        response = client.get_access_key_last_used(
            AccessKeyId=self.compromised_resource['access_key_id']
        )
        username = response['UserName']
        return username

    def __generate_inline_policy(self):
        template_name = './aws_ir/templates/deny-sts-before-time.json.j2'
        template_file = open(template_name)
        template_contents = template_file.read()
        jinja_template = Template(template_contents)
        policy_document = jinja_template.render(
            before_date=self.__get_date()
        )
        return policy_document

    def __attach_inline_policy(self, username, policy_document):
        client = boto3.client(
            'iam',
            region_name='us-east-1'
        )

        response = client.put_user_policy(
            UserName=username,
            PolicyName="threatresponse-temporal-key-revocation",
            PolicyDocument=policy_document
        )
        return response
