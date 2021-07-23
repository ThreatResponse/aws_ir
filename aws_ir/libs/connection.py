import boto3
import logging
import os

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, type, service=None, region='us-west-2', profile='default'):
        self.region = region
        self.connection_type = type
        self.service = service
        self.client = None
        self.resource = None
        self.profile = profile
        self.aws_access_key_id= os.getenv('AWS_ACCESS_KEY_ID', None)
        self.aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY', None)
        self.aws_session_token = os.getenv('AWS_SESSION_TOKEN', None)
        try:
            session_kwargs = {}
            session_kwargs['profile_name'] = self.profile
            if self.aws_access_key_id is not None:
                session_kwargs["aws_access_key_id"] = self.aws_access_key_id
                logger.debug("Took access key id from env")
            if self.aws_secret_access_key is not None:
                session_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
                logger.debug("Took secret access key from env")
            if self.aws_session_token is not None:
                session_kwargs["aws_session_token"] = self.aws_session_token
                logger.debug("Took session token from env")
            else:
                session_kwargs['profile_name'] = self.profile
                logger.debug("No session token in the env, setting profile name instead")
            boto3.setup_default_session(**session_kwargs)
        except Exception as e:
            logger.info("Problem setting default boto3 session: {}".format(e))

    def connect(self):
        if self.connection_type is None:
            raise AttributeError(
                "Could not determine connect type.  Set client or resource."
            )
        elif self.connection_type == "client":
            client = boto3.client(
                self.service,
                region_name=self.region
            )
            self.client = client
            return self.client
        elif self.connection_type == "resource":
            resource = boto3.resource(
                self.service,
                region_name=self.region
            )
            self.resource = resource
            return self.resource
        elif self.connection_type == "session":
            try:
                session = boto3.Session(
                    region_name=self.region,
                    profile_name=self.profile
                )
                logger.info(
                    "Returning session for default profile."
                )
            except Exception as e:
                logger.info(
                    "We are likely running on AWS instance.: {}".format(e)
                )
                session = boto3.Session(
                    region_name=self.region
                )
            return session
        else:
            raise AttributeError(
                "Connection type is not supported."
            )
