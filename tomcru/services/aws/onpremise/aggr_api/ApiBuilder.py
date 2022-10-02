import os.path
from typing import Dict

from eme.entities import load_handlers
from flask import request

from tomcru import TomcruApiDescriptor, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruLambdaIntegrationDescription, TomcruSwaggerIntegration
from .ApiGwBuilderCore import ApiGwBuilderCore

from .controllers.EmeProxyController import EmeProxyController
from .controllers.HomeController import HomeController
from .integration.SwaggerIntegration import SwaggerIntegration, integrate_swagger_ui_blueprint

from .integration.TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration
from .integration.LambdaIntegration import LambdaIntegration

from .apps.EmeWebApi import EmeWebApi


class ApiBuilder(ApiGwBuilderCore):

    def build_api(self, api_name, api: TomcruApiDescriptor, env: str):
        self.env = env

        # build eme app object
        apiopts = self.apigw_cfg.get('__default__', {})
        apiopts.update(self.apigw_cfg.get(api_name, {}))

        # todo: @LATER: decide between implementation detail, e.g. fastapi | flask | eme-flask
        #app_type = apiopts['app_type']
        app = self.create_app(api_name, apiopts)

        self._inject_dependencies()

        self._build_authorizers()
        _controllers, _index = self._build_controllers(api)

        self.load_eme_handlers(_controllers, _index)

        self._clean_dependencies()

        return app

    def _build_controllers(self, api):

        # build controllers
        _controllers = {}
        _index = None
        _swagger: Dict[str, TomcruSwaggerIntegration | None] = {"json": None, "html": None, "yaml": None}

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():
            _controllers.setdefault(ro.group, EmeProxyController(ro.group, self.on_request))

            endpoint: TomcruEndpointDescriptor
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None

                _integration: TomcruApiGWHttpIntegration

                if isinstance(endpoint, TomcruLambdaIntegrationDescription):
                    # build lambda integration
                    _integration = LambdaIntegration(endpoint, auth, self.p.serv('aws:onpremise:lambda_b'), env=self.env)
                elif isinstance(endpoint, TomcruSwaggerIntegration):
                    _swagger[endpoint.req_content] = endpoint

                    if endpoint.req_content != 'html':
                        _integration = SwaggerIntegration(api, endpoint, auth, env=self.env)
                    else:
                        continue
                else:
                    # todo: for now we assume it's always lambda
                    raise NotImplementedError()

                # refer to integration (proxy controller refers to self.on_request)
                self.integrations[endpoint] = _integration

                # pass endpoint to proxy controller, so that it constructs correct routing (needed for eme apps)
                _controllers[ro.group].add_method(endpoint, lambda x: NotImplementedError())
                # app type dependent integration (eme-webapp | flask | fastapi | eme-websocket)
                self.add_method(endpoint)

                if endpoint.route == '/':
                    _index = endpoint.endpoint_id

        # create swagger UI (both ui and json endpoints are needed)
        if api.swagger_enabled and api.swagger_ui and _swagger:
            # todo: integrate with yaml too? can this be decided? does swagger UI allow even?
            integrate_swagger_ui_blueprint(self.app, _swagger['json'], _swagger['html'])

        return _controllers, _index

    def on_request(self, **kwargs):
        """
        Flask integration for endpoint request
        :param kwargs: flask url params
        :return: flask response obj
        """
        # get called endpoint
        ep = self.get_called_endpoint(**kwargs)
        integ = self.integrations[ep]

        response = integ.on_request(**kwargs)

        # HTTP in flask needs a return response, et voilà
        return response

    def create_app(self, api_name, apiopts):
        self.app = EmeWebApi(self.cfg.apis[api_name], apiopts)

        return self.app

    def load_eme_handlers(self, _controllers, _index=None):
        # add api index controller
        if _index is None:
            _index = "Home:get_index"
            _controllers['Home'] = HomeController(self.app)

        webcfg = {"__index__": _index}

        # @TODO: @later: add swagger pages? generate them or what?
        self.app.load_controllers(_controllers, webcfg)

        # include custom controllers
        _app_path = os.path.join(self.cfg.app_path, 'controllers')
        if os.path.exists(_app_path):
            self.app.load_controllers(load_handlers(self.app, 'Controller', path=_app_path), webcfg)

    def add_method(self, endpoint: TomcruEndpointDescriptor, fn_to_call=None):
        """
        Adds method to EME/Flask app
        :param app: eme app (flask app)
        :param endpoint: endpoint url to hook to
        """
        # replace AWS APIGW route scheme to flask routing schema
        _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        self.app._custom_routes[endpoint.endpoint_id].add(_api_route)

    def get_called_endpoint_id(self) -> str:
        """
        Gets abstract endpoint id from flask request
        :return:
        """
        ep = request.endpoint
        group, method_name = ep.split(':')
        method, integ_id = method_name.split("_")

        # todo: but isn't this the exact same as request.endpoint?
        return f'{group}:{method.lower()}_{integ_id}'

    def get_called_endpoint(self) -> TomcruEndpointDescriptor:
        aws_url_rule = str(request.url_rule).replace('<', '{').replace('>', '}')

        # todo: @later: maybe we can optimize by fetching api directly
        api = next(filter(lambda x: aws_url_rule in x.routes, self.cfg.apis.values()))
        route = api.routes[aws_url_rule]

        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        return endpoint
