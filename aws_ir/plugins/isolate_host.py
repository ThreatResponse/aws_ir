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
        self.examiner_cidr_range = compromised_resource['examiner_cidr_range']
        self.dry_run = dry_run

        self.setup()

    def setup(self):
        sg = self.__create_isolation_security_group()
        acl = self.__create_network_acl()
        connections_stopped = self.__add_network_acl_entries(acl)

        """Conditions that can not be dry_run"""
        if self.dry_run == False:
            self.__add_security_group_rule(sg)
            egress_revoked = self.__revoke_egress(sg)
            instance_shifted = self.__add_security_group_to_instance(sg)
        pass

    def validate(self):
        """Validate that the instance is in fact isolated"""
        if self.sg_name != None:
            return True
        else:
            return False

    def __create_isolation_security_group(self):
        try:
            security_group_result = self.client.create_security_group(
                DryRun=self.dry_run,
                GroupName=self.__generate_security_group_name(),
                Description="ThreatResponse Isolation Security Group",
                VpcId=self.compromised_resource['vpc_id'],

            )

        except Exception as e:
            try:
                if e.response['Error']['Message'] == """
                Request would have succeeded, but DryRun flag is set.
                """:
                    security_group_result['GroupId'] = None
            except:
                raise e
        return security_group_result['GroupId']

    def __add_security_group_rule(self, security_group_id):
        try:
            self.client.authorize_security_group_ingress(
                DryRun=self.dry_run,
                GroupId=security_group_id,
                IpProtocol='tcp',
                FromPort=22,
                ToPort=22,
                CidrIp=self.examiner_cidr_range
            )
        except Exception as e:
            try:
                if e.response['Error']['Message'] == """
                Request would have succeeded, but DryRun flag is set.
                """:
                    pass
            except:
                raise e

    def __revoke_egress(self, group_id):
        try:
            response = self.client.revoke_security_group_egress(
                DryRun=self.dry_run,
                GroupId=group_id
            )

            return True
        except:
            return False

    def __generate_security_group_name(self):
        sg_name = "isolation-sg-{case_number}-{instance}-{uuid}".format(
            case_number=self.compromised_resource['case_number'],
            instance=self.compromised_resource['instance_id'],
            uuid=str(uuid.uuid4())
        )
        self.sg_name = sg_name
        return sg_name

    def __add_security_group_to_instance(self, group_id):
        try:
            response = self.client.modify_instance_attribute(
                DryRun=self.dry_run,
                InstanceId=self.compromised_resource['instance_id'],
                Groups=[
                    group_id,
                ],
            )
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
            try:
                if e.response['Error']['Message'] == """
                Request would have succeeded, but DryRun flag is set.
                """:
                    return None
            except:
                raise e

    def __add_network_acl_entries(self, acl_id):
        try:
            response = self.client.create_network_acl_entry(
                DryRun=self.dry_run,
                NetworkAclId=acl_id,
                RuleNumber=1300,
                Protocol='-1',
                RuleAction='allow',
                Egress=False,
                CidrBlock=self.examiner_cidr_range
            )

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
        except Exception as e:
            try:
                if e.response['Error']['Message'] == """
                Request would have succeeded, but DryRun flag is set.
                """:
                    return None
            except:
                raise e
