import base64
import boto3

"""Gathers ephemeral data that could be lost on instance termination"""

class Gather(object):
    """
        Initializer takes standard plugin constructor
        added api flag for data persistence in AWS_IR
        api
    """
    def __init__(
        self,
        client,
        compromised_resource,
        dry_run,
        api=False
    ):

        self.client = client
        self.compromised_resource = compromised_resource
        self.compromise_type = compromised_resource['compromise_type']
        self.dry_run = dry_run
        self.api = api

        """
            These attrs will only be set during API=True
            Added for Readability and AWS_IR data persistence
        """
        self.evidence = {}

        self.setup()

    def setup(self):
        if self.dry_run != True:
            metadata = self.__get_aws_instance_metadata()
            self.__log_aws_instance_metadata(metadata)
            console = self.__get_aws_instance_console_output()
            self.__log_aws_instance_console_output(console)
            self.__log_aws_instance_screenshot()
            return True
        else:
            return False

    def validate(self):
        """ Can't really validate data gather """
        return True

    def __get_aws_instance_metadata(self):
        metadata = self.client.describe_instances(
                         Filters=[
                            {
                                'Name': 'instance-id',
                                'Values': [
                                    self.compromised_resource['instance_id']
                                ]
                            }
                        ]
                    )['Reservations']

        return metadata

    def __log_aws_instance_metadata(self, data):
        if self.api == True:
            self.evidence['metadata.json'] = data
        else:
            logfile = ("/tmp/{case_number}-{instance_id}-metadata.log").format(
                case_number=self.compromised_resource['case_number'],
                instance_id=self.compromised_resource['instance_id']
            )
            with open(logfile,'w') as w:
                w.write(str(data))

    def __get_aws_instance_console_output(self):
        output = self.client.get_console_output(
            InstanceId=self.compromised_resource['instance_id']
        )
        return output

    def __log_aws_instance_console_output(self, data):
        if self.api == True:
            self.evidence['console.json'] = data
        else:
            logfile = ("/tmp/{case_number}-{instance_id}-console.log").format(
                case_number=self.compromised_resource['case_number'],
                instance_id=self.compromised_resource['instance_id']
            )
            with open(logfile,'w') as w:
                w.write(str(data))

    def __log_aws_instance_screenshot(self):
        response = self.client.get_console_screenshot(
               InstanceId=self.compromised_resource['instance_id'],
               WakeUp=True
        )
        if self.api == True:
            self.evidence['screenshot.jpg'] = response['ImageData']
        else:
            logfile = ("/tmp/{case_number}-{instance_id}-screenshot.jpg").format(
                case_number=self.compromised_resource['case_number'],
                instance_id=self.compromised_resource['instance_id']
            )

            fh = open(logfile, "wb")
            fh.write(base64.b64decode(response['ImageData']))
            fh.close()
