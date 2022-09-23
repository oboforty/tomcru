from typing import Dict

from tomcru import TomcruApiDescriptor, TomcruProject, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruApiLambdaAuthorizerDescriptor, TomcruApiAuthorizerDescriptor, TomcruLambdaIntegrationDescription
from tomcru.core import utils

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

        # todo: @LATER: decide between implementation detail, e.g. fastapi | flask | eme-flask
        #app_type = apiopts['app_type']
        if 'http' == api.api_type:
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
                else:
                    self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.apigw_cfg, self.lambda_builder)

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

                _integration: TomcruApiGWHttpIntegration

                if isinstance(endpoint, TomcruLambdaIntegrationDescription):
                    # build lambda
                    self.lambda_builder.build_lambda(endpoint)
                    _integration = LambdaIntegration(endpoint, auth, self.lambda_builder)
                else:
                    # todo: for now we assume it's always lambda
                    raise NotImplementedError()

                # refer to integration (proxy controller refers to self.on_request)
                self.integrations[endpoint] = _integration

                # pass endpoint to proxy controller, so that it constructs correct routing (needed for eme apps)
                _controllers[ro.group].add_method(endpoint, lambda x: NotImplementedError())
                # app type dependent integration (eme-webapp | flask | fastapi | eme-websocket)
                self.imp.add_method(endpoint)

        return _controllers

    def _inject_dependencies(self):
        """
        Injects boto3 and lambda layers for all lambda integrations
        """

        #self.boto3_injector.inject_boto3()
        # inject boto3
        boto3, boto3_path = self.boto3_builder.build_boto3(self.imp)
        utils.inject('boto3', boto3_path, boto3)

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
