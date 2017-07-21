import boto3


class Connection(object):
    def __init__(self, type, service=None, region='us-west-2', profile='default'):
        self.region = region
        self.connection_type = type
        self.service = service
        self.client = None
        self.resource = None
        self.profile = profile
        try:
            boto3.setup_default_session(profile_name=self.profile)
        except Exception as e:
            raise(e)

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
            session = boto3.Session(
                region_name=self.region,
                profile_name=self.profile
            )
            return session
        else:
            raise AttributeError(
                "Connection type is not supported."
            )
