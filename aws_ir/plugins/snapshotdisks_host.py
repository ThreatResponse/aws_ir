import boto3

class Snapshotdisks(object):
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

        self.session = boto3.Session(
                    region_name=self.compromised_resource['region']
        )

        self.setup()

    def setup(self):
        self.__snapshot_volumes()

    def __create_snapshot(self, volume_id, description):
        try:
            response = self.client.create_snapshot(
                DryRun=self.dry_run,
                VolumeId=volume_id,
                Description=description
            )
            return response
        except Exception as e:
            if e.response['Error']['Message'] == """
            Request would have succeeded, but DryRun flag is set.
            """:
                return None
            else:
                return e

    def __tag_snapshot(self, snapshot_id):
        ec2 = self.session.resource('ec2')
        snapshot = ec2.Snapshot(snapshot_id)
        snapshot.create_tags(
            Tags=[
                dict(
                    Key='cr-case-number',
                    Value=self.compromised_resource['case_number']
                )
            ]
        )

    def __snapshot_volumes(self):
        for volume_id in self.compromised_resource['volume_ids']:
            description = 'Snapshot of {vid} for case {cn}'.format(
                vid=volume_id,
                cn=self.compromised_resource['case_number']
            )

            snapshot = self.__create_snapshot(volume_id, description)
            if snapshot != None:
                snapshot_id = snapshot['SnapshotId']
                self.__tag_snapshot(snapshot_id)
        pass
