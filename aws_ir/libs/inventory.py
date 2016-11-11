import os
import boto3
import json
import pprint
import time

import urllib.request
from datetime import datetime, timedelta

class Inventory(object):
  def __init__(self, client, regions):
    self.client = client
    self.regions = regions

    if os.environ.get('EDDA_SERVER'):
        self.inventory = self.get_all_running_from_edda()
    else:
        self.inventory = self.get_all_running_from_aws()

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
      reservations = urllib.request.urlopen("http://172.16.31.127:8080/api/v2/view/instances/;_all")
      reservations = json.loads(reservations.read().decode())
      for instance in reservations:
          instance_data = self.__extract_data_edda(instance)
          if instance_data['region'] == region:
              inventory.append(instance_data)
      return inventory

  def __extract_data_aws(self, instance, region):
    return dict(
      public_ip_address = instance.get('PublicIpAddress', None),
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
