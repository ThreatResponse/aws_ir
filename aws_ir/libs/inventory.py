import logging

logger = logging.getLogger(__name__)


class Query(object):
    def __init__(self, client, regions, inventory_type='aws'):
        self.client = client
        self.regions = regions
        self.type = inventory_type
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
                instance_data = self._extract_data_aws(instance, region)
                instance_data['region'] = region
                inventory.append(instance_data)
        return inventory

    def _extract_data_aws(self, instance, region):
        return dict(
            public_ip_address=instance.get('PublicIpAddress', None),
            private_ip_address=instance.get('PrivateIpAddress', None),
            instance_id=instance['InstanceId'],
            launch_time=instance['LaunchTime'],
            platform=instance.get('Platform', None),
            vpc_id=instance['VpcId'],
            ami_id=instance['ImageId'],
            volume_ids=[
                bdm['Ebs']['VolumeId']
                for bdm in instance.get(
                    'BlockDeviceMappings', []
                )
            ],
            region=region
        )

    def get_all_running_from_aws(self):
        inventory = {}
        for region in self.regions:
            logger.info(("Searching {region} for instance.".format(region=region)))
            inventory[region] = self.get_running_by_region_aws(region)
        return inventory


class InventoryType(object):
    def __init__(self):
        self.type = self._inventory_type()

    def _inventory_type(self):
        return "aws"


class Inventory(object):
    def __init__(self, client, regions):
        self.client = client
        self.regions = regions
        self.type = 'aws'

        self.inventory = Query(
            self.client,
            self.regions,
            self.type
        ).result

    def locate_instance_by_ip(self, ip):
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

    def locate_instance_by_id(self, instance_id):
        for region in self.regions:
            located = list(
                filter(
                    lambda x: x['instance_id'] == instance_id,
                    self.inventory[region]
                )
            )

            if len(located) == 0:
                pass
            else:
                return located[0]
