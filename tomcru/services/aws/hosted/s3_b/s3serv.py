from tomcru.services.ServiceBase import ServiceBase


class S3Service(ServiceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ddb = None

    def init(self):
        pass
