import boto3

class nullCloudTrail(object):
    def __init__(self):
        self.client = None
        self.regions = None
        self.trail_list = None

    @property
    def has_trails(self):
        return False

class CloudTrail(object):
    def __init__(self, regions, client):
        self.client = client
        self.regions = regions
        self.trail_list = self.get_aws_cloudtrails()

    def get_client(self, region):
        try:
            self.client.region = region
            client = self.client.connect()
            return client
        except:
            return None

    def get_aws_cloudtrails(self):
        try:
            for region in self.regions:
                self.client = self.get_client(region)
                response = self.client.describe_trails(
                    includeShadowTrails=True
                )
                return response
        except:
            return None

    @property
    def has_trails(self):
        if len(self.trail_list['trailList']) > 0:
            return True
        else:
            return False
