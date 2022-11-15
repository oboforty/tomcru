import os.path
from typing import Dict

from tomcru import TomcruCfg, TomcruProject, TomcruEndpointDescriptor, TomcruApiLambdaAuthorizerDescriptor, TomcruApiOIDCAuthorizerDescriptor
from tomcru.core import utils

from .integration.LambdaAuthorizerIntegration import LambdaAuthorizerIntegration
from .integration.ExternalLambdaAuthorizerIntegration import ExternalLambdaAuthorizerIntegration
from .integration.TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration, TomcruApiGWAuthorizerIntegration
from .integration.OIDCAuthorizerIntegration import OIDCAuthorizerIntegration

class ApiGwBuilderCore:

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.cfg: TomcruCfg = project.cfg
        self.p = project

        # params passed to Integrators:
        self.apigw_cfg = apigw_cfg
        self.boto3_builder = self.p.serv('aws:onpremise:boto3_b')
        self.integrations: Dict[TomcruEndpointDescriptor, TomcruApiGWHttpIntegration] = {}
        self.authorizers: Dict[str, TomcruApiGWAuthorizerIntegration] = {}
        self.env: str | None = None
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

            elif isinstance(auth, TomcruApiOIDCAuthorizerDescriptor):
                self.authorizers[authorizer_id] = OIDCAuthorizerIntegration(auth, self.apigw_cfg, env=self.env)
            else:
                # todo: implement IAM and jwt
                raise NotImplementedError(authorizer_id)

    def _inject_layers(self):
        """
        Injects lambda layers for all lambda integrations
        """

        # inject layers
        if self.cfg.layers:
            _layers_paths = list(map(lambda f: os.path.join(self.cfg.app_path, 'layers', f[3]), self.cfg.layers))
            _layers_keywords = set(map(lambda f: f[1][0], self.cfg.layers))
            utils.inject(_layers_keywords, _layers_paths)

    def _clean_layers(self):
        utils.cleanup_injects()
