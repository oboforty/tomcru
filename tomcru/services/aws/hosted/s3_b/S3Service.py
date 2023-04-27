from deepmerge import always_merger

from tomcru.services.ServiceBase import ServiceBase

from .S3AdapterLocal import S3AdapterLocal


class S3Service(ServiceBase):
    INIT_PRIORITY = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3: S3AdapterLocal | None = None

    def init(self):

        # todo: handle remote adapters (http/ftp upload)

        self.s3 = S3AdapterLocal(self.env.app_path, self.cfg, self.opts)

        self.service('boto3').add_resource('s3', self.s3)
