import boto3
class Connection(object):
    def __init__(self, type, service, region=None):
        self.region = region
        self.connection_type = type
        self.service = service
        self.client = None
        self.resource = None

    def connect(self):
        if self.connection_type is None:
            raise StandardError(
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
        else:
            raise StandardError(
                "Connection type is not supported."
            )
