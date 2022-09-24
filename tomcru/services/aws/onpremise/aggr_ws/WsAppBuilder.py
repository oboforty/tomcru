import os.path
from typing import Dict

from eme.entities import load_handlers
from flask import request

from tomcru import TomcruApiDescriptor, TomcruProject, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruApiLambdaAuthorizerDescriptor, TomcruApiAuthorizerDescriptor, TomcruLambdaIntegrationDescription

from .apps.EmeWsApp import EmeWsApp
from .aggr_api_utils import ApiGwBuilderCore, TomcruApiGWHttpIntegration
from .integration.LambdaIntegration import LambdaIntegration


class WsAppBuilder(ApiGwBuilderCore):

    def __init__(self, project: TomcruProject, apigw_cfg):
        super().__init__(project, apigw_cfg)

        #self.api_serv = self.p.serv('aws:onpremise:aggr_api')

    def build_api(self, api_name, api: TomcruApiDescriptor, env: str):
        self.env = env

        # build eme app object
        apiopts = self.apigw_cfg.get('__default__', {})
        apiopts.update(self.apigw_cfg.get(api_name, {}))

        self.app = EmeWsApp(self.cfg.apis[api_name], apiopts)

        self._inject_dependencies()

        self._build_authorizers()
        self._build_groups(api)

        self._clean_dependencies()

        return self.app

    def _build_groups(self, api):

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():

            endpoint: TomcruLambdaIntegrationDescription
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None

                _integration: TomcruApiGWHttpIntegration

                if isinstance(endpoint, TomcruLambdaIntegrationDescription):
                    # build lambda integration
                    _integration = LambdaIntegration(self.app, endpoint, auth, self.p.serv('aws:onpremise:lambda_b'), env=self.env)
                else:
                    # todo: for now we assume it's always lambda
                    raise NotImplementedError()

                # refer to integration (proxy controller refers to self.on_request)
                self.integrations[endpoint] = _integration
