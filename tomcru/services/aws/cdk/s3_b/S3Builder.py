import logging
import os.path


from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class S3Builder(ServiceBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inject_dependencies(self):
        pass

    def init(self):
        app = self.service('cdk_app')

        for bucket_name, bucket_cfg in self.cfg.get('buckets').items():
            # TODO

            bucket = app.cdk.s3.Bucket(
                app.stacks['base'],
                "Bucket",
                # bucket_name=bucket_name,
                # encryption=app.cdk.s3.BucketEncryption.S3_MANAGED,
                # enforce_ssl=True,
                # access_control=app.cdk.s3.BucketAccessControl.PRIVATE,
                # object_ownership=app.cdk.s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                # block_public_access=app.cdk.s3.BlockPublicAccess.BLOCK_ALL,
                # versioned=True,
                # server_access_logs_bucket=logs_bucket,
                # auto_delete_objects=self.s3.get_removal_policy()
                # == RemovalPolicy.DESTROY,
                # removal_policy=self.s3.get_removal_policy(),
                # cors=cors,
                # lifecycle_rules=self.get_s3_lifecycle_rules(
                #     self.s3.bucket,
                #     intelligent_tiering_days=self.s3.primary_intelligent_tiering_transition_days,
                # ),
            )
