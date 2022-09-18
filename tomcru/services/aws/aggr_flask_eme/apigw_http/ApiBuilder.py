import os

from eme.entities import load_handlers

from tomcru import TomcruApiDescriptor, TomcruProject, TomcruEndpointDescriptor, TomcruRouteDescriptor

from .apps.EmeWebApi import EmeWebApi
from .controllers.EmeProxyController import EmeProxyController
from .controllers.HomeController import HomeController
from .integration.LambdaIntegration import LambdaIntegration
from .integration.AuthorizerIntegration import AuthorizerIntegration


class ApiBuilder:

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.cfg = project.cfg
        self.apigw_cfg = apigw_cfg
        self.p = project

        self.lambda_builder = self.p.serv('aws:onpremise:lambda_b')

    def build_api(self, api_name, api: TomcruApiDescriptor) -> EmeWebApi:
        # build eme app object
        apiopts = self.apigw_cfg.get('__default__', {})
        apiopts.update(self.apigw_cfg.get(api_name, {}))

        app = EmeWebApi(self.cfg, apiopts)

        # build authorizers

        # build controllers

        #self.p.serv('aws:local_mock:boto3_b').inject_boto()

        _controllers = {}

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():
            _controllers.setdefault(ro.group, EmeProxyController(ro.group, self.on_request))

            endpoint: TomcruEndpointDescriptor
            for endpoint in ro.endpoints:
                fn = self.lambda_builder.build_lambda(endpoint)

                # pass lambda fn to controller
                _controllers[ro.group].add_method(endpoint, fn)
                self.add_method(app, endpoint)

        self.load_eme_handlers(app, _controllers)

        #self.p.serv('aws:local_mock:boto3').detach_boto()

        return app

    def on_request(self, **kwargs):
        integ = LambdaIntegration()

        evt = integ.get_event(**kwargs)
        resp = self.lambda_builder.run_lambda(integ.get_called_lambda(), evt)
        return integ.parse_response(resp)

    def add_method(self, app: EmeWebApi, endpoint: TomcruEndpointDescriptor):
        # replace AWS APIGW route scheme to flask routing schema
        _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        app._custom_routes[endpoint.endpoint_id].add(_api_route)

    def load_eme_handlers(self, app, _controllers):
        # add api index controller
        webcfg = {"__index__": "Home:get_index"}
        _controllers['Home'] = HomeController(app)

        # @TODO: @later: add swagger pages? generate them or what?
        app.load_controllers(_controllers, webcfg)

        # include custom controllers
        _app_path = os.path.join(self.cfg.app_path, 'controllers')
        if os.path.exists(_app_path):
            app.load_controllers(load_handlers(app, 'Controller', path=_app_path), webcfg)

