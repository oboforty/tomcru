import os

from tomcru.core import utils
from .boto3 import Boto3
from tomcru import TomcruProject


class Boto3Builder:

    def __init__(self, project: TomcruProject, opts: dict):
        self.p = project
        self.cfg = project.cfg
        self.boto3_cfg = opts
        self.objs = project.serv('aws:onpremise:obj_store')

        self.boto3_obj: Boto3 | None = None

    def init(self):
        """
        Builds onpremsie boto3 wrapper

        :param apigw_app_wrapper: local api implementation `
        :return:
        """
        self.boto3_obj = Boto3(self.objs)

        return self.boto3_obj

    def inject(self):
        """
        Injects mocked boto3 object as importable python package
        """
        _path = os.path.dirname(os.path.realpath(__file__))

        utils.inject('boto3', _path, self.boto3_obj)

    def deject(self):
        utils.clean_inject('boto3')
