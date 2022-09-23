from typing import Dict

from tomcru import TomcruApiDescriptor, TomcruProject, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruApiLambdaAuthorizerDescriptor, TomcruApiAuthorizerDescriptor, TomcruLambdaIntegrationDescription
from tomcru.core import utils

#from flask import request

from .controllers.EmeProxyController import EmeProxyController
from .integration.LambdaIntegration import LambdaIntegration
from .integration.AuthorizerIntegration import LambdaAuthorizerIntegration, ExternalLambdaAuthorizerIntegration
from .integration.TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration, TomcruApiGWAuthorizerIntegration
from .implementations.EmeWebAppIntegrator import EmeWebAppIntegrator


class ApiBuilder:

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.cfg = project.cfg
        self.p = project

        # params passed to Integrators:
        self.apigw_cfg = apigw_cfg
        self.lambda_builder = self.p.serv('aws:onpremise:lambda_b')
        self.boto3_builder = self.p.serv('aws:onpremise:boto3_b')
        self.integrations: Dict[TomcruEndpointDescriptor, TomcruApiGWHttpIntegration] = {}
        self.authorizers: Dict[str, TomcruApiGWAuthorizerIntegration] = {}
        self.imp = None

    def build_api(self, api_name, api: TomcruApiDescriptor):
        # build eme app object
        apiopts = self.apigw_cfg.get('__default__', {})
        apiopts.update(self.apigw_cfg.get(api_name, {}))

        app_type = apiopts['app_type']
        if 'eme-flask' == app_type:
            self.imp = EmeWebAppIntegrator(self.p, self.apigw_cfg)
            app = self.imp.create_app(apiopts)
        else:
            raise NotImplementedError()

        self._inject_dependencies()

        self._build_authorizers()
        _controllers = self._build_controllers(api)

        self.imp.load_eme_handlers(_controllers)

        utils.cleanup_injects()

        return app

    def _build_authorizers(self):
        # build authorizers
        for authorizer_id, auth in self.cfg.authorizers.items():
            if isinstance(auth, TomcruApiLambdaAuthorizerDescriptor):
                # evaluate lambda sub type
                if 'external' == auth.lambda_source:
                    self.authorizers[authorizer_id] = ExternalLambdaAuthorizerIntegration(auth, self.apigw_cfg)
                elif 'internal' == auth.lambda_source:
                    self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.apigw_cfg, self.lambda_builder)
                else:
                    raise Exception("Incorrect lambda source: " + auth.lambda_source)

            else:
                # todo: implement IAM and jwt
                raise NotImplementedError(authorizer_id)

    def _build_controllers(self, api):

        # build controllers
        _controllers = {}

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():
            _controllers.setdefault(ro.group, EmeProxyController(ro.group, self.on_request))

            endpoint: TomcruLambdaIntegrationDescription
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None
                # todo: how to evaluate integration type? for now we assume it's always lambda
                self.integrations[endpoint] = LambdaIntegration(endpoint, auth, self.lambda_builder)

                # pass lambda fn to controller
                _controllers[ro.group].add_method(endpoint, lambda x: NotImplementedError())
                self.imp.add_method(endpoint)

                #fn = self.lambda_builder.build_lambda(endpoint)
                #_integ = LambdaIntegration(self.lambda_builder, endpoint, )

        return _controllers

    def _inject_dependencies(self):
        """
        Injects boto3 and lambda layers for all lambda integrations
        """

        #self.boto3_injector.inject_boto3()
        # inject boto3
        self.boto3_builder.build_boto3(self, self.imp)

        # inject layers
        if self.cfg.layers:
            _layers_paths = list(map(lambda f: f[3], self.cfg.layers))
            _layers_keywords = set(map(lambda f: f[1][0], self.cfg.layers))
            utils.inject(_layers_keywords, _layers_paths)

    def on_request(self, **kwargs):
        """
        Flask integration for endpoint request
        :param kwargs: flask url params
        :return: flask response obj
        """
        # get called endpoint
        ep = self.imp.get_called_endpoint()
        integ = self.integrations[ep]

        response = integ.on_request(**kwargs)

        # HTTP in flask needs a return response, et voilà
        return response
