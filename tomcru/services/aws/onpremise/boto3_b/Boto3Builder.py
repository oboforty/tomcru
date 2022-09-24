import os
from typing import Tuple

from .services.boto3 import Boto3
from tomcru import TomcruProject


class Boto3Builder:

    def __init__(self, project: TomcruProject, opts: dict):
        self.p = project
        self.cfg = project.cfg
        self.boto3_cfg = opts

    def build_boto3(self, apigw_app_wrapper) -> Tuple[Boto3, str]:
        """
        Builds onpremsie boto3 wrapper

        :param apigw_app_wrapper: local api implementation `
        :return:
        """

        # @todo: later: apiGW service depends on individual API, but we should map api to ID (use global FaaSAppBuilder instead of ApiBuilder)
        b = Boto3(apigw_app_wrapper, self.cfg.app_path, self.boto3_cfg)
        _path = os.path.dirname(os.path.realpath(__file__))

        return b, os.path.join(_path, 'services')
