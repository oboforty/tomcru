import os

from tomcru.services.ServiceBase import ServiceBase
from tomcru.core import utils


__dir__ = os.path.dirname(os.path.realpath(__file__))


class ApiGWWebsocketBuilder(ServiceBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self):
        """
        :return:
        """
        pass
