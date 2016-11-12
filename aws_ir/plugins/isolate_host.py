import uuid
import boto3

class Isolate(object):
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
        self.security_group = self.setup()

    def setup(self):
        sg = self.__create_isolation_security_group()
        acl = self.__create_network_acl()
        connections_stopped = self.__add_network_acl_entry(acl)

        """Conditions that can not be dry_run"""
        if self.dry_run == False:
            egress_revoked = self.__revoke_egress(sg)
            instance_shifted = self.__add_security_group_to_instance(sg)
        pass

    def __create_isolation_security_group(self):
        try:
            security_group_result = self.client.create_security_group(
                DryRun=self.dry_run,
                GroupName=self.__generate_security_group_name(),
                Description="ThreatResponse Isolation Security Group",
                VpcId=self.compromised_resource['vpc_id'],

            )
        except Exception as e:
            if e.response['Error']['Message'] == """
            Request would have succeeded, but DryRun flag is set.
            """:
                security_group_result['GroupId'] = None
            else:
                return e
        return security_group_result['GroupId']

    def __revoke_egress(self, group_id):
        try:
            session = boto3.Session(
                region_name=self.compromised_resource['region']
            )
            ec2 = session.resource('ec2')
            sg = ec2.SecurityGroup(group_id)
            sg.revoke_egress(IpPermissions=sg.ip_permissions_egress)
            return True
        except:
            return False

    def __generate_security_group_name(self):
        sg_name = "isolation-sg-{case_number}-{instance}-{uuid}".format(
            case_number=self.compromised_resource['case_number'],
            instance=self.compromised_resource['instance_id'],
            uuid=str(uuid.uuid4())
        )
        return sg_name

    def __add_security_group_to_instance(self, group_id):
        try:
            session = boto3.Session(
                region_name=self.compromised_resource['region']
            )
            ec2 = session.resource('ec2')
            i = ec2.Instance(self.compromised_resource['instance_id'])
            i.modify_attribute(Groups=[group_id,])
            return True
        except:
            return False

    def __create_network_acl(self):
        try:
            response = self.client.create_network_acl(
                DryRun=self.dry_run,
                VpcId=self.compromised_resource['vpc_id'],
            )
            return response['NetworkAcl']['NetworkAclId']
        except Exception as e:
            if e.response['Error']['Message'] == """
            Request would have succeeded, but DryRun flag is set.
            """:
                return None
            else:
                return e

    def __add_network_acl_entry(self, acl_id):
        response = self.client.create_network_acl_entry(
            DryRun=self.dry_run,
            NetworkAclId=acl_id,
            RuleNumber=1337,
            Protocol='-1',
            RuleAction='deny',
            Egress=True,
            CidrBlock="{compromised_host_private_ip}/32".format(
                compromised_host_private_ip=self.compromised_resource['private_ip_address']
            )
        )
        return True
