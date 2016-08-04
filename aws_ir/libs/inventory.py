import boto3
from datetime import datetime, timedelta

class Inventory(object):
  def __init__(self, client, regions):
    self.client = client
    self.regions = regions
    self.inventory = self.get_all_running()

  def get_running_by_region(self, region):
    inventory = []
    self.client.region = region
    client = self.client.connect()

    reservations = client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )['Reservations']

    for reservation in reservations:
      for instance in reservation['Instances']:
          instance_data = self.__extract_data(instance, region)
          instance_data['region'] = region
          inventory.append(instance_data)
    return inventory

  def __extract_data(self, instance, region):
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

  def get_all_running(self):
    inventory = {}

    for region in self.regions:
      inventory[region] = self.get_running_by_region(region)
    return inventory

  def recent(self, hours_ago=48):
      recent = []
      delta = datetime.today() - timedelta(hours = hours_ago)
      for region in self.regions:
          for instance in self.inventory[region]:
              stripped_time = str(instance['launch_time']).split('+')
              if datetime.strptime(str(stripped_time[0]), "%Y-%m-%d %H:%M:%S") > delta:
                  recent.append(dict(instance))
      return recent

  def locate_instance(self, ip):
      for region in self.regions:
        located = filter(
        lambda x: x['public_ip_address'] == ip,
        self.inventory[region]
        )
        if len(located) == 0:
            pass
        else:
            return located[0]
