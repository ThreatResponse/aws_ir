import uuid

"""Class to create the cases s3 bucket for asset storage"""


class CaseBucket(object):
    def __init__(self, case_number, region, client, resource):
        self.region = region
        self.case_number = case_number
        self.client = client
        self.s3 = resource.connect()
        self.bucket = self.find_or_create_by()

    def find_or_create_by(self):
        bucket = self._locate_bucket()
        if bucket is not None:
            return bucket
        else:
            self.bucket_name = self._generate_name()
            bucket = self._create_s3_bucket()
            self._set_acls(self.bucket_name)
            self._set_tags(self.bucket_name)
            self._set_versioning(self.bucket_name)
            return bucket
        pass

    def cleanup_empty_buckets(self):
        buckets = self.client.list_buckets()
        for bucket in buckets['Buckets']:
            if str(bucket['Name']).find('cloud-response') != -1:
                try:
                    self.client.delete_bucket(Bucket=bucket['Name'])
                    print(bucket['Name'])
                except Exception:
                    pass

    def _generate_name(self):
        bucket_name = 'cloud-response-' + str(uuid.uuid4()).replace('-', '')
        return bucket_name

    def _create_s3_bucket(self):
        # the if statement is to prevent
        # a fun little bug https://github.com/boto/boto3/issues/125
        if self.region == 'us-east-1':
            bucket = self.s3.create_bucket(
                Bucket=self.bucket_name
            )
        else:
            bucket = self.s3.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.region
                }
            )
        return bucket

    def _set_acls(self, bucket_name):
        self.s3.BucketAcl(bucket_name).put(ACL='bucket-owner-full-control')

    def _set_tags(self, bucket_name):
        self.client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging=dict(
                TagSet=[
                    dict(
                        Key='cr-case-number',
                        Value=self.case_number
                    )
                ]
            )
        )

    def _set_versioning(self, bucket_name):
        self.client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration=dict(
                MFADelete='Disabled',
                Status='Enabled'
            )
        )

    def _locate_bucket(self):
        buckets = self.s3.buckets.all()
        for bucket in buckets:
            if bucket.name.startswith("cloud-response-"):
                tags = self._get_bucket_tags(bucket.name)
                if self._check_tags(tags):
                    case_bucket = bucket
                    return case_bucket
                else:
                    return None
            else:
                pass

    def _get_bucket_tags(self, bucket):
        try:
            s3 = self.client
            response = s3.get_bucket_tagging(
                Bucket=bucket,
            )
        except Exception:
            response = None
        return response

    def _check_tags(self, tag_object):
        if tag_object is None:
            return False
        elif tag_object.get('TagSet', None) is not None:
            for tag in tag_object['TagSet']:
                if tag['Value'] == self.case_number:
                    return True
                else:
                    return False
        else:
            return False
