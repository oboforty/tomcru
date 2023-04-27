import os

from tomcru.services.ServiceBase import ServiceBase
from tomcru.core import utils
from .boto3 import Boto3


__dir__ = os.path.dirname(os.path.realpath(__file__))


class Boto3Builder(ServiceBase):
    INIT_PRIORITY = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.boto3_obj: Boto3 | None = None
        self.boto3_obj = Boto3(self.get_resource, self.opts.get('allowed.clients', cast=set), self.opts.get('allowed.resources', cast=set))

    def init(self):
        """
        Builds onpremsie boto3 wrapper

        :param apigw_app_wrapper: local api implementation `
        :return:
        """

        return self.boto3_obj

    def inject_dependencies(self):
        """
        Injects mocked boto3 object as importable python package
        """

        if self.boto3_obj is None:
            raise Exception("Boto3Builder: mock hasn't been initialized yet!")

        utils.inject('boto3', __dir__, self.boto3_obj)

    def deject_dependencies(self):
        utils.clean_inject('boto3')

    def add_resource(self, res_id, res):
        return self.service('obj_store').add('boto3', res_id, res)

    def get_resource(self, res_id):
        return self.service('obj_store').get('boto3', res_id)
