import boto3

class Stop(object):
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
        if self.dry_run != True:
            self.__stop_instance()
        else:
            pass

    def __stop_instance(self):
        response = self.client.stop_instances(
            InstanceIds=[
                self.compromised_resource['instance_id']
            ],
            Force=True
        )
        return response
