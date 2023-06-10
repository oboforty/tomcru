import os

from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


class IamBuilder(ServiceBase):
    INIT_PRIORITY = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.credentials = {}

    def init(self):
        creds = self.opts.get('credentials', {})
        if isinstance(creds, list):
            if len(creds) == 0:
                creds = {}
            elif isinstance(creds[0], dict):
                creds = {d['key']: d['secret'] for d in creds}
            elif isinstance(creds[0], (list, tuple)):
                creds = dict(creds)
        self.credentials = creds

    def get_secret_from_key(self, aws_key):
        return self.credentials.get(aws_key)
