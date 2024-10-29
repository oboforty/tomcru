import logging
import os.path


from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class DynamoDBBuilder(ServiceBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inject_dependencies(self):
        pass

    def init(self):
        pass
