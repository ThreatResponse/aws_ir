import os
import sys
import boto3
import json
import pprint
import time

if sys.version_info[0] == 3:
    import urllib.request as request
else:
    import urllib2 as request
from datetime import datetime, timedelta

class Query(object):
  def __init__(self, client, regions, inventory_type):
    self.client = client
    self.regions = regions

    if inventory_type == "edda":
        self.result = self.get_all_running_from_edda()
    else:
        self.result = self.get_all_running_from_aws()

  def get_running_by_region_aws(self, region):
    inventory = []
    self.client.region = region
    client = self.client.connect()

    reservations = client.describe_instances(
          Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
          )['Reservations']

    for reservation in reservations:
        for instance in reservation['Instances']:
            instance_data = self.__extract_data_aws(instance, region)
            instance_data['region'] = region
            inventory.append(instance_data)
    return inventory

  def get_running_by_region_edda(self, region):
    inventory = []

    edda_url = self.__edda_url()
    api_call = "{edda_url}view/instances/;_all".format(edda_url=edda_url)
    reservations = request.urlopen(api_call)
    reservations = json.loads(reservations.read().decode())
    for instance in reservations:
        instance_data = self.__extract_data_edda(instance)
        if instance_data['region'] == region:
            inventory.append(instance_data)

    return inventory

  def __edda_url(self):
      server = os.environ.get('EDDA_SERVER')
      port = os.environ.get('EDDA_PORT')
      base_url = os.environ.get('EDDA_BASE_URL')

      edda_url = "http://{server}:{port}{base_url}".format(
        server=server,
        port=port,
        base_url=base_url
      )
      return edda_url

  def __extract_data_aws(self, instance, region):
    return dict(
        public_ip_address = instance.get('PublicIpAddress', None),
        private_ip_address = instance.get('PrivateIpAddress', None),
        instance_id = instance['InstanceId'],
        launch_time = instance['LaunchTime'],
        platform = instance.get('Platform', None),
        vpc_id = instance['VpcId'],
        ami_id = instance['ImageId'],
        volume_ids = [ bdm['Ebs']['VolumeId'] for bdm in instance.get('BlockDeviceMappings', [] ) ],
        region = region
    )

  def __extract_data_edda(self, instance):
    return dict(
        public_ip_address = instance.get('publicIpAddress', None),
        private_ip_address = instance.get('privateIpAddress', None),
        instance_id = instance['instanceId'],
        launch_time =  instance['launchTime'],
        platform = instance.get('platform', None),
        vpc_id = instance['vpcId'],
        ami_id = instance['imageId'],
        volume_ids = [ bdm['ebs']['volumeId'] for bdm in instance.get('blockDeviceMappings', [] ) ],
        region = str(instance['placement']['availabilityZone'])[:-1]
    )

  def get_all_running_from_aws(self):
    inventory = {}
    for region in self.regions:
        inventory[region] = self.get_running_by_region_aws(region)
    return inventory

  def get_all_running_from_edda(self):
    inventory = {}
    for region in self.regions:
        inventory[region] = self.get_running_by_region_edda(region)
    return inventory

class InventoryType(object):
    def __init__(self):
        self.type = self.__inventory_type()

    def __inventory_type(self):
        if os.environ.get('EDDA_SERVER'):
            return "edda"
        else:
            return "aws"

class Inventory(object):
  def __init__(self, client, regions):
    self.client = client
    self.regions = regions

    self.type = InventoryType().type

    self.inventory = Query(
        self.client,
        self.regions,
        self.type
    ).result

  def locate_instance(self, ip):
      for region in self.regions:
        located = list(
            filter(
                lambda x: x['public_ip_address'] == ip,
                self.inventory[region]
            )
        )

        if len(located) == 0:
            pass
        else:
          return located[0]
