import boto3

class AmazonWebServices(object):
    def __init__(self, client):
        self.client = client
        self.regions = self.__get_regions()
        self.availability_zones = self.__get_availability_zones()

    def __get_regions(self):
        """ Use the provided AWS Client to iterate over the regions and store them """
        availRegions = []
        regions = self.client.connect().describe_regions()
        for region in regions['Regions']:
            availRegions.append(region['RegionName'])
        return availRegions

    def __get_availability_zones(self):
        """ Use the provided AWS Client to iterate over the azs and store them """
        availZones = []
        for region in self.regions:
            self.client.region = region
            client = self.client.connect()
            zones = client.describe_availability_zones()['AvailabilityZones']
            for zone in zones:
                if zone['State'] == 'available':
                    availZones.append(zone['ZoneName'])
        return availZones
