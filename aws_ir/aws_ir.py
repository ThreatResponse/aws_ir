#!/usr/bin/env python
from datetime import datetime, timedelta
import pprint
import boto3
import logging
import os
import random
import requests
import subprocess
import sys
import tempfile
import time
import uuid
import json
import base64
import margaritashotgun

import settings


from libs import ts_logger

from libs import connection
from libs import aws
from libs import s3bucket
from libs import inventory
from libs import cloudtrail

class DisableOwnKeyError(RuntimeError):
    """ Thrown when a request is made to disable the current key being used.  """
    pass
class MissingDependencyError(RuntimeError):
    """ Thrown when this program is missing a dependency. """
    pass

class AWS_IR(object):
    case_type = ''
    def __init__(self, examiner_cidr_range='0.0.0.0/0', case_number=None, bucket=None):
        self.create_time = datetime.utcnow()
        self.case_number = case_number
        self.logger = logging.getLogger('aws_ir.cli')
        streamhandler = logging.StreamHandler(sys.stdout)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        streamhandler.setFormatter(formatter)
        self.logger.addHandler(streamhandler)

        self.inventory = []
        self.examiner_cidr_range = examiner_cidr_range

        self.session = boto3.Session()
        self.json_entries = []
        self.bucket = None

    @property
    def case_number(self):
        return self._case_number

    @case_number.setter
    def case_number(self, case_number):
        if case_number is None:
            self._case_number = datetime.utcnow().strftime(
                'cr-%y-%m%d%H-{0:04x}'
                ).format(
                    random.randint(0,2**16)
            )
        else:
            self._case_number = case_number

    def event_to_logs(self, message):
        json_event = ts_logger.timesketch_logger(message, self.case_number)
        json_event
        self.logger.info(message)

    def mitigate(self):
        raise NotImplementedError('Use HostCompromise or KeyCompromise')

    def setup(self):
        """ Get all the required information before doing the mitigation. """
        client = connection.Connection(
            type='client',
            service='ec2'
        ).connect()

        self.event_to_logs("Initial connection to AmazonWebServices made.")
        self.amazon = aws.AmazonWebServices(
            connection.Connection(
                type='client',
                service='ec2'
            )
        )

        self.available_regions = self.amazon.regions

        self.event_to_logs("Inventory AWS Regions Complete {region_count} found.".format(
                region_count = len(self.amazon.regions)
            )
        )

        self.availability_zones = self.amazon.availability_zones

        self.event_to_logs(
                "Inventory Availability Zones Complete {zone_count} found.".format(
                zone_count = len(self.amazon.availability_zones)
            )
        )

        self.event_to_logs(
                "Beginning inventory of instances world wide.  This might take a minute..."
        )

        self.aws_inventory = inventory.Inventory(
            connection.Connection(
                type='client',
                service='ec2'
            ),
            self.available_regions
        )

        self.event_to_logs(
                "Inventory complete.  Proceeding to resource identification."
        )

        self.inventory = self.aws_inventory.inventory
        self.recent_instances = self.aws_inventory.recent()

        self.log_aws_recent_instances(self.recent_instances)
        self.trail_logs = cloudtrail.CloudTrail(
            regions = self.amazon.regions,
            client = connection.Connection(
                    type='client',
                    service='cloudtrail'
                )
            ).trail_list

    def setup_bucket(self, region):
        if self.bucket == None:
            self.bucket = s3bucket.CaseBucket(self.case_number, region).bucket.name

    def rename_log_file(self, case_number, resource_id):
        os.rename(
            ("/tmp/{case_number}-aws_ir.log").format(
                case_number=case_number,
                ),
            ("/tmp/{case_number}-{resource_id}-aws_ir.log").format(
                case_number=case_number,
                resource_id=resource_id
                )
        )

    def teardown(self, region, resource_id):
        """ Any final post mitigation steps """
        #Rename log file to include instance or key_id
        self.rename_log_file(self.case_number, resource_id)
        self.copy_logs_to_s3()
        processing_end_messaging = (
            """Processing complete : Launch an analysis workstation with the command \n
                {caller} -n {case_number} create_workstation {region} \n
            """
        ).format(case_number=self.case_number, caller="aws_ir", region=region)
        print(processing_end_messaging)

    def get_case_logs(self):
        files = []
        for file in os.listdir("/tmp"):
            if file.startswith(self.case_number):
                files.append(file)
        return files

    def copy_logs_to_s3(self):
        s3 = boto3.resource('s3')
        case_bucket = s3.Bucket(self.bucket)
        logs = self.get_case_logs()
        for log in logs:
            case_bucket.upload_file(str("/tmp/" + log), log)

    def get_aws_session(self, region='us-west-2'):
        session = boto3.Session(
             region_name=region
        )
        return session

    def create_aws_isolation_sg(self, region, vpc_id, instance_id):
        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()
        session = self.get_aws_session(region=region)
        description = "Lanched by AWS IR for Case " + self.case_number
        sg_name = "isolation-sg-{case_number}-{instance}-{uuid}".format(
            case_number=self.case_number,
            instance=instance_id,
            uuid=str(uuid.uuid4())
        )
        sg = client.create_security_group(
            GroupName=sg_name, Description=description, VpcId=vpc_id
        )
        self.event_to_logs("Security Group Created " + sg['GroupId'])
        ec2 = session.resource('ec2')
        security_group_id = sg['GroupId']
        isolate_sg = ec2.SecurityGroup(security_group_id)
        isolate_sg.revoke_egress(IpPermissions=isolate_sg.ip_permissions_egress)
        self.event_to_logs("Security Group Egress Access Revoked for " + sg['GroupId'])
        return sg['GroupId']

    def add_aws_isolation_sg_rule(
        self,
        security_group_id,
        region,
        authorized_cidr_range,
        port,
        proto
    ):
        session = self.get_aws_session(region=region)
        ec2 = session.resource('ec2')
        isolate_sg = ec2.SecurityGroup(security_group_id)
        isolate_sg.authorize_ingress(
            IpProtocol=proto,
            CidrIp=authorized_cidr_range,
            FromPort=port,
            ToPort=port
        )
        self.event_to_logs(
        "Access Ingress Added for proto={proto} from={port} to={port} cidr_range={authorized_cidr_range} for sg={sg}".format(
            proto=proto,
            port=port,
            authorized_cidr_range=authorized_cidr_range,
            sg=security_group_id
        ))

    def get_aws_instance_metadata(self, instance_id, region):
        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()
        metadata = client.describe_instances(
                         Filters=[{'Name': 'instance-id', 'Values': [instance_id]}]
                         )['Reservations']
        return metadata

    def log_aws_instance_metadata(self, instance_id, data):
        logfile = ("/tmp/{case_number}-{instance_id}-metadata.log").format(
            case_number=self.case_number, instance_id=instance_id
        )
        with open(logfile,'w') as w:
            w.write(str(data))

    def get_aws_instance_console_output(self, instance_id, region):
        client = connection.Connection(
                    type='client',
                    service='ec2',
                    region=region
                ).connect()
        output = client.get_console_output(InstanceId=instance_id)
        return output

    def log_aws_instance_console_output(self, instance_id, data):
        logfile = ("/tmp/{case_number}-{instance_id}-console.log").format(
            case_number=self.case_number, instance_id=instance_id
        )
        with open(logfile,'w') as w:
            w.write(str(data))

    def log_aws_instance_screenshot(self, instance_id, region):

        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()

        response = client.get_console_screenshot(
               InstanceId=instance_id,
               WakeUp=True
        )
        logfile = ("/tmp/{case_number}-{instance_id}-screenshot.jpg").format(
            case_number=self.case_number, instance_id=instance_id
        )
        fh = open(logfile, "wb")
        fh.write(base64.b64decode(response['ImageData']))
        fh.close()

    def add_incident_tag_to_instance(self, instance_dict):
        region = instance_dict['region']
        instance_id = instance_dict['instance_id']
        client = connection.Connection(
                type='client',
                service='ec2',
                region=region
        ).connect()
        session = self.get_aws_session(region=region)
        ec2 = session.resource('ec2')
        tag = [{'Key': 'cr-case-number','Value': self.case_number}]
        client.create_tags(Resources=[instance_id], Tags=tag)

    def disable_access_key(self, access_key_id, force_disable_self=False):
        session = boto3.session.Session()
        own_access_key_ids = [ x['aws_access_key_id'] for x in session._session.__dict__['_config']['profiles'].itervalues() ]
        if access_key_id  in own_access_key_ids  and force_disable_self is not True:
            raise DisableOwnKeyError()

        client = self.session.client('iam')

        # we get the username for the key because even though username is optional
        # if the username is not provided, the key will not be found, contrary to what
        # the documentation says.
        response = client.get_access_key_last_used(AccessKeyId=access_key_id)
        username = response['UserName']

        client.update_access_key(UserName=username, AccessKeyId=access_key_id, Status='Inactive')
        self.event_to_logs('Set satus of access key {0} to Inactive'.format(access_key_id))

    def snapshot_volumes(self, volume_ids, region):
        if not isinstance(volume_ids, list):
            volume_ids = [ volume_ids ]

        client = connection.Connection(
                type='client',
                service='ec2',
                region=region
        ).connect()

        session = self.get_aws_session(region=region)
        ec2 = session.resource('ec2')
        responses = []
        for volume_id in volume_ids:
            description = 'Snapshot of {vid} for case {cn}'.format(vid=volume_id, cn=self.case_number)
            snapshot_response = client.create_snapshot(VolumeId=volume_id, Description=description)
            snapshot_id = snapshot_response['SnapshotId']
            self.event_to_logs('Took a snapshot of volume {vid} to snapshot {sid}'.format(vid=volume_id, sid=snapshot_id))

            #add tag to snapshot
            snapshot = ec2.Snapshot(snapshot_id)
            snapshot.create_tags(Tags=[dict(
                Key='cr-case-number',
                Value=self.case_number
            )])

            responses.append(snapshot_response)

        return responses

    def populate_examiner_cidr_range(self):
        r = requests.get('http://ipecho.net/plain')
        ip_addr = r.text.strip()
        self.examiner_cidr_range = ip_addr + "/32"

    def stop_instance(self, instance_id, region, force=False ):
        client = connection.Connection(
                    type='client',
                    service='ec2',
                    region=region
        ).connect()

        response = client.stop_instances(
            InstanceIds=[instance_id],
            Force=force
        )
        self.event_to_logs('Stopping instance: instance_id={0}'.format(instance_id))
        return response

    def set_aws_instance_security_group(self, instance_id, sg, region):
        session = self.get_aws_session(region=region)
        ec2 = session.resource('ec2')
        i = ec2.Instance(instance_id)
        i.modify_attribute(Groups=[sg,])
        self.event_to_logs('Shifted instance into isolate security group.')
        pass

    def log_aws_recent_instances(self, recent):
         logfile = ("/tmp/{case_number}-recent_instances.log").format(
             case_number=self.case_number
         )
         with open(logfile,'w') as w:
             w.write(str(recent))

class CreateWorkstation(AWS_IR):
    """ Creats an IR Workstation instance """
    def __init__(self, examiner_cidr_range, case_number=None, key_name=None, region=None):
        self.key_name = key_name
        self.private_key = None
        self.region = region
        super(CreateWorkstation, self).__init__(examiner_cidr_range, case_number=case_number)

    def prep_key(self, region):

        if self.key_name is not None:
            return self.key_name

        self.key_directory = tempfile.mkdtemp(prefix='ws_keys_')
        private_key_handle, self.private_key = tempfile.mkstemp(suffix='.pem',prefix=self.case_number)
        key_name = os.path.basename(self.private_key)

        client = connection.Connection(
                    type='client',
                    service='ec2',
                    region=region
        ).connect()

        response = client.create_key_pair(KeyName=key_name)

        os.write(private_key_handle, response['KeyMaterial'])
        os.close(private_key_handle)

        self.event_to_logs('Wrote new key to {0}'.format(self.private_key))

        return key_name

    def get_roles(self, response=None):
        if response is None:
            response = self.iam_client.list_roles()
            return self.get_roles(response)
        if response['IsTruncated'] == False:
            return response['Roles']
        roles = response['Roles']
        new_response = self.iam_client.list_roles(Marker=response['Marker'])
        return roles + get_roles(new_response)

    def prep_iam_role(self, region):
        role_name = (
            "cloudresponse_workstation-{case_number}-{region}"
        ).format(
            case_number=self.case_number,
            region=region
        )
        self.iam_client = connection.Connection(
                    type='client',
                    service='iam'
        ).connect()

        roles = self.get_roles()
        role_search = filter(lambda x: x['RoleName'] == role_name, roles)
        if len(role_search) == 1:
            self.event_to_logs('Found policy: {0}'.format(role_name))
            self.instance_profile = role_name
            return role_name

        assume_policy_document = dict(Version="2012-10-17", Statement=[
            dict(
                Sid='',
                Effect='Allow',
                Principal=dict(Service="ec2.amazonaws.com"),
                Action="sts:AssumeRole"
            )
        ])
        response = self.iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(
                assume_policy_document
                )
            )
        self.event_to_logs('Created policy: {0}'.format(role_name))

        policies = [
            'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
            'arn:aws:iam::aws:policy/IAMFullAccess',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AWSCloudTrailReadOnlyAccess'
        ]

        for policy in policies:
            response = self.iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy)
            self.event_to_logs('Attaching policy {policy} to role {role}'.format(policy=policy, role=role_name))

        response = self.iam_client.create_instance_profile(InstanceProfileName=role_name)
        self.event_to_logs('Created instance profile with name {0} and ID {1}'.format(role_name, response['InstanceProfile']['InstanceProfileId']))

        # instance profile needs a few seconds before it is ready
        time.sleep(30)

        response = self.iam_client.add_role_to_instance_profile(InstanceProfileName=role_name, RoleName=role_name)
        self.event_to_logs('Attached role {0} to instance profile {0}'.format(role_name))
        self.instance_profile = role_name

        # instance profile needs a few seconds before it is ready
        time.sleep(5)

        return role_name

    def launch_ami(self, region, ami_id, key_name, role_name, security_group_id):
        client = connection.Connection(
                    type='client',
                    service='ec2',
                    region=region
        ).connect()
        script = """#!/bin/bash
echo CASE_NUMBER="$CASE_NUMBER" >> /opt/threatresponse/.env
chmod -R 777 /opt/timesketch/contrib/*_data
docker pull threatresponse/threatresponse:latest
cd /opt/threatresponse && /usr/local/bin/docker-compose up -d
cd /opt/timesketch && /usr/local/bin/docker-compose up -d
"""

        script = script.replace('$CASE_NUMBER', self.case_number)
        response = client.run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            SubnetId=self.subnet_id,
            IamInstanceProfile=dict(Name=self.instance_profile),
            BlockDeviceMappings=[{"DeviceName": "/dev/xvda","Ebs" : { "VolumeSize" : 64 }}],
            InstanceType='m3.large',
            UserData=script
        )

        instance_id = response['Instances'][0]['InstanceId']
        self.event_to_logs(
            'Launching AMI {ami_id} to instace id {instance_id}'.format(
                ami_id=ami_id,instance_id=instance_id
                )
            )
        return instance_id

    def create_security_group(self, region):
        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()
        response = client.create_vpc(CidrBlock='10.0.0.0/16')
        self.vpc_id = response['Vpc']['VpcId']
        self.event_to_logs('Created new security vpc {0}'.format(self.vpc_id))

        response = client.modify_vpc_attribute(
            VpcId=self.vpc_id,
            EnableDnsHostnames=dict(
                Value=True
                )
            )

        group_name = ('cloudresponse_workstation-{case_number}_sg').format(
            case_number=self.case_number
        )
        description = 'A security group for the cloudresponse workstation'
        response = client.create_security_group(GroupName=group_name, Description=description, VpcId=self.vpc_id)
        self.sg_id = response['GroupId']
        self.event_to_logs('Created new security group {0}'.format(self.sg_id))

        self.add_aws_isolation_sg_rule(self.sg_id, region, self.examiner_cidr_range, 22, 'tcp')

        response = client.create_subnet(VpcId=self.vpc_id, CidrBlock='10.0.1.0/24')
        self.subnet_id = response['Subnet']['SubnetId']
        self.event_to_logs('Created new subnet with id {0}'.format(self.subnet_id))

        response = client.modify_subnet_attribute(SubnetId=self.subnet_id, MapPublicIpOnLaunch=dict(Value=True))
        return self.sg_id

    def create_internet_gateway(self, region, timeout_seconds=300):
        ''' This code isn't needed, but I just finished writing it and don't have the heart to delete it yet '''
        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()
        response = client.create_internet_gateway()
        internet_gateway_id = response['InternetGateway']['InternetGatewayId']
        self.event_to_logs('Created InternetGateway with ID {0}'.format(internet_gateway_id))

        response = client.attach_internet_gateway(InternetGatewayId=internet_gateway_id, VpcId=self.vpc_id)
        self.event_to_logs('Attaching InternetGateway {0} to VPC {1}'.format(internet_gateway_id, self.vpc_id))
        attached=False
        for i in range(timeout_seconds):
            self.event_to_logs(
                'Checking if InternetGateway {0} is attached to VPC {1}'.format(
                    internet_gateway_id,
                    self.vpc_id
                    )
                )
            response = client.describe_internet_gateways(InternetGatewayIds=[internet_gateway_id])
            if is_internet_gateway_attached(response, internet_gateway_id, self.vpc_id):
                attached=True
                break
            time.sleep(1)
        if not attached:
            raise RuntimeError('Could not attach IG to VPC')

        self.internet_gateway_id = internet_gateway_id

        ec2 = boto3.resource('ec2')
        vpc = ec2.Vpc(self.vpc_id)
        response = client.describe_route_tables(Filters=[dict(Name='vpc-id', Values=[self.vpc_id])])
        route_table_id = response['RouteTables'][0]['RouteTableId']
        client.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0',GatewayId=internet_gateway_id)

        return self.internet_gateway_id

    def get_public_ip(self, region, timeout_seconds=300):
        client = connection.Connection(
            type='client',
            service='ec2',
            region=region
        ).connect()

        instance = None
        for i in range(timeout_seconds):
            self.event_to_logs('Checking if instance {0} is running.'.format(self.instance_id))
            response = client.describe_instances(InstanceIds=[self.instance_id])
            instance = running_instance_or_none(response, self.instance_id)
            if instance is not None:
                break
            time.sleep(1)
        if instance is None:
            raise RuntimeError('Timeout out waiting for instance to start')

        ip_address = instance['PublicIpAddress']
        self.event_to_logs('Instance {0} is running at {1}'.format(self.instance_id, ip_address))
        return ip_address

    def format_ssh_command(self, ip_address, username='ec2-user'):
        command = 'ssh -i {key_path} -L9999:127.0.0.1:9999 -L5000:127.0.0.1:5000 -L3000:127.0.0.1:3000 {username}@{ip} {extra}'
        if self.private_key is not None:
            key_path = self.private_key
            extra = ''
        else:
            key_path = 'path/to/{0}'.format(self.key_name)
            extra = '# Be sure to specify the correct path for the private key'
        return command.format(key_path=key_path, username=username, ip=ip_address, extra=extra)

    def create(self):

        AMI_ID = settings.AMI_IDS[self.region]
        # 1. Generate SSH Key pair (if key not specified)
        key_name = self.prep_key(region=self.region)

        # 2. Create / Find IAM Role
        role_name = self.prep_iam_role(region=self.region)

        # 3. Create security group
        security_group_id = self.create_security_group(region=self.region)

        # 4. Create and attach internet gateway
        internet_gateway_id = self.create_internet_gateway(region=self.region)

        # 5. Launch instance into user's account with IAM Role and pub key
        self.instance_id = self.launch_ami(self.region, AMI_ID, key_name, role_name, security_group_id)

        # 6. Tag instance with case reference number
        client = connection.Connection(
                type='client',
                service='ec2',
                region=self.region
        ).connect()

        tag = [
            {'Key': 'cr-case-number','Value': self.case_number},
            {'Key': 'cr-workstation','Value': 'true'},
        ]
        client.create_tags(Resources=[self.instance_id], Tags=tag)


        # 7. Provide user with login info.
        ip_address = self.get_public_ip(self.region)
        command = self.format_ssh_command(ip_address)
        self.event_to_logs('connect to the workstation instance with: {0}'.format(command))
        print('connect to the workstation instance with: \n {0}'.format(command))

def is_internet_gateway_attached(response, internet_gateway_id, vpc_id):
    ig_search = filter(lambda x: x['InternetGatewayId'] == internet_gateway_id, response['InternetGateways'])
    if len(ig_search) == 0:
        raise ValueError('Could not find InternetGateway with ID {0}'.format(internet_gateway_id))
    ig = ig_search[0]
    attachment_search = filter(lambda x: x['VpcId'] == vpc_id, ig['Attachments'])
    if len(attachment_search) == 0:
        raise ValueError('Could not find VPC {0} on InternetGateway with ID {1}'.format(vpc_id, internet_gateway_id))
    attachment = attachment_search[0]
    return attachment['State'] == 'attached' or attachment['State'] == 'available'

def running_instance_or_none(response, instance_id):
    instance_list = []
    for x in response['Reservations']:
        instance_list.extend(x['Instances'])
    instance_search = filter(lambda x: x['InstanceId'] == instance_id, instance_list)
    if len(instance_search) == 0:
        raise ValueError('Could not find instance with ID {0}'.format(instance_id))
    instance = instance_search[0]
    if instance['State']['Name'] == 'running':
        return instance
    return None

class HostCompromise(AWS_IR):
    """ Procedures for responding to a HostCompromise.

        ** For now, assume only Linux system.

    """
    case_type = 'Host'
    def __init__(self,
            user, ssh_key_file,
            examiner_cidr_range='0.0.0.0/0',
            compromised_host_ip=None,
            case_number=None,
            bucket=None,
            prog=None
        ):
        if compromised_host_ip==None:
            raise ValueError('Must specifiy an IP for the compromised host')
        if not os.path.exists(ssh_key_file):
            raise ValueError('Key file must exist. Could not find path {0}'.format(ssh_key_file))

        self.prog = prog
        self.ssh_key_file_path = ssh_key_file
        self.user = user


        self.compromised_host_ip = compromised_host_ip
        super(HostCompromise, self).__init__(examiner_cidr_range, case_number=case_number, bucket=bucket)

    def isolate(self):
        """
            - Create a new secrurity group.
            - Add a rule to allow SSH from examiner IP.
            - Apply the SG to our compromised instance.
        """
        # create security group
        sg_id = self.create_aws_isolation_sg(
            self.inventory_compromised_host['region'],
            self.inventory_compromised_host['vpc_id'],
            self.inventory_compromised_host['instance_id'],
        )
        self.add_aws_isolation_sg_rule(
            sg_id,
            self.inventory_compromised_host['region'],
            self.examiner_cidr_range,
            22,
            'tcp'
        )
        self.set_aws_instance_security_group(
            self.inventory_compromised_host['instance_id'],
            sg_id,
            self.inventory_compromised_host['region']
        )

    def create_snapshots(self):
        volume_ids = self.inventory_compromised_host['volume_ids']
        region = self.inventory_compromised_host['region']

        responses = self.snapshot_volumes(volume_ids, region)
        self.snapshot_ids = [ sr['SnapshotId'] for sr in responses ]

    def get_memory(self, bucket, ip, user, key, case_num, port=None, password=None):
        name = 'margaritashotgun'
        config = dict(aws = dict(bucket = bucket),
                      hosts = [ dict(addr = ip, port = port,
                                    username = user,
                                    password = password,
                                    key = key) ],
                      workers = 'auto',
                      logging = dict(log_dir = '/tmp/',
                                     prefix = ("{case_num}-{ip}").format(
                                                  ip=ip,
                                                  case_num=case_num )),
                      repository = dict(enabled = True,
                                        url = ('https://threatresponse-lime'
                                               '-modules.s3.amazonaws.com/')))
        capture_client = margaritashotgun.client(name=name, config=config,
                                                 library=True, verbose=True)
        # returns {'total': ..., 'failed': [ip, ip, ...], 'completed': [ip, ip, ...]}
        return capture_client.run()

    def mitigate(self):
        self.setup()

        search = self.aws_inventory.locate_instance(self.compromised_host_ip)
        if search == None:
            raise ValueError('Compromised IP Address not found in inventory.')
        self.inventory_compromised_host = search

        self.setup_bucket(self.inventory_compromised_host['region'])

        # step 1 - isolate
        self.isolate()

        # step 2 - apply compromised tag
        self.add_incident_tag_to_instance(self.inventory_compromised_host)

        # step 3 - get instance metadata and store it
        self.instance_metadata = self.get_aws_instance_metadata(
            self.inventory_compromised_host['instance_id'],
            self.inventory_compromised_host['region']
        )

        self.log_aws_instance_metadata(
            self.inventory_compromised_host['instance_id'],
            self.instance_metadata
        )

        self.instance_console_output = self.get_aws_instance_console_output(
            self.inventory_compromised_host['instance_id'],
            self.inventory_compromised_host['region']
        )

        self.log_aws_instance_console_output(
            self.inventory_compromised_host['instance_id'],
            self.instance_console_output
        )

        self.log_aws_instance_screenshot(
            self.inventory_compromised_host['instance_id'],
            self.inventory_compromised_host['region']
        )

        # step 4 - create snapshot
        self.create_snapshots()


        # step 5 - gather memory
        if self.inventory_compromised_host['platform'] == 'windows':
            self.event_to_logs('Platform is Windows skipping live memory')
        else:
            self.event_to_logs(
                "Attempting run margarita shotgun for {user} on {ip} with {keyfile}".format(
                    user=self.user,
                    ip=self.compromised_host_ip,
                    keyfile=self.ssh_key_file_path
                    )
                )
            try:

                results = self.get_memory(self.bucket, self.compromised_host_ip,
                                          self.user, self.ssh_key_file_path,
                                          self.case_number)
                self.event_to_logs(("memory capture completed for: {0}, "
                                    "failed for: {1}".format(results['completed'],
                                                             results['failed'])))
            except Exception as ex:
                # raise keyboard interrupt passed during memory capture
                if isinstance(ex, KeyboardInterrupt):
                    raise
                else:
                    self.event_to_logs(
                        ( "Memory acquisition failure with exception"
                          "{exception}. ".format(exception=ex) )
                    )


        # step 6 - shutdown instance
        self.stop_instance(
            self.inventory_compromised_host['instance_id'],
            self.inventory_compromised_host['region']
        )
        self.teardown(
            region=self.inventory_compromised_host['region'],
            resource_id=self.inventory_compromised_host['instance_id']
        )

class KeyCompromise(AWS_IR):
    case_type = 'Key'
    def __init__(self,
            examiner_cidr_range='0.0.0.0/0',
            compromised_access_key_id=None,
            case_number=None,
            bucket=None,
            region=None
        ):
        if compromised_access_key_id==None:
            raise ValueError('Must specifiy an access_key_id for the compromised key.')
        self.compromised_access_key_id = compromised_access_key_id
        self.region = region
        super(KeyCompromise, self).__init__(
            examiner_cidr_range,
            case_number=case_number,
            bucket=bucket
        )

    def mitigate(self):
        self.setup()
        self.setup_bucket(region=self.region)

        # step 1 - disable access key
        self.disable_access_key(self.compromised_access_key_id)
        self.teardown(
            region=self.region,
            resource_id=self.compromised_access_key_id
        )
