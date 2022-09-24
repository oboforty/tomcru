import os.path
from typing import Dict

from tomcru import TomcruCfg, TomcruProject, TomcruEndpointDescriptor, TomcruApiLambdaAuthorizerDescriptor
from tomcru.core import utils

from .integration.AuthorizerIntegration import LambdaAuthorizerIntegration, ExternalLambdaAuthorizerIntegration
from .integration.TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration, TomcruApiGWAuthorizerIntegration


class ApiGwBuilderCore:

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.cfg: TomcruCfg = project.cfg
        self.p = project

        # params passed to Integrators:
        self.apigw_cfg = apigw_cfg
        self.boto3_builder = self.p.serv('aws:onpremise:boto3_b')
        self.integrations: Dict[TomcruEndpointDescriptor, TomcruApiGWHttpIntegration] = {}
        self.authorizers: Dict[str, TomcruApiGWAuthorizerIntegration] = {}
        self.env: str = None
        self.app = None

    def _build_authorizers(self):
        # build authorizers
        for authorizer_id, auth in self.cfg.authorizers.items():
            if isinstance(auth, TomcruApiLambdaAuthorizerDescriptor):
                # evaluate lambda sub type
                if 'external' == auth.lambda_source:
                    self.authorizers[authorizer_id] = ExternalLambdaAuthorizerIntegration(auth, self.apigw_cfg)
                else:
                    self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.apigw_cfg, self.p.serv('aws:onpremise:lambda_b'), env=self.env)

            else:
                # todo: implement IAM and jwt
                raise NotImplementedError(authorizer_id)

    def _inject_dependencies(self):
        """
        Injects boto3 and lambda layers for all lambda integrations
        """

        #self.boto3_injector.inject_boto3()
        # inject boto3
        boto3, boto3_path = self.boto3_builder.build_boto3(self.app)
        utils.inject('boto3', boto3_path, boto3)

        # inject layers
        if self.cfg.layers:
            _layers_paths = list(map(lambda f: os.path.join(self.cfg.app_path, 'layers', f[3]), self.cfg.layers))
            _layers_keywords = set(map(lambda f: f[1][0], self.cfg.layers))
            utils.inject(_layers_keywords, _layers_paths)

    def _clean_dependencies(self):
        utils.cleanup_injects()
