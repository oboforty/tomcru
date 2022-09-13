from eme.website import WebsiteApp

from tomcru.core import TomcruApiDescriptor, TomCruProject, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruCfg
from .controllers.EmeProxyController import EmeProxyController
from .integration.lambda_integ import LambdaIntegration


class ApiBuilder:

    def __init__(self, project: TomCruProject):
        self.cfg = project.cfg
        self.p = project

        self.lambda_builder = self.p.serv('aws:onpremise:lambda')

    def build_api(self, api_name, api: TomcruApiDescriptor, app: WebsiteApp):

        # build authorizers

        # build controllers

        self.p.serv('aws:local_mock:boto3').inject_boto()

        _controllers = {}

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():
            # todo: itt: custom controller HTTP-nek
            # todo es controlleren belul ne legyen ciganymagia
            if ro.group not in _controllers:
                _controllers[ro.group] = EmeProxyController(ro.group, self.on_request)

            endpoint: TomcruEndpointDescriptor
            for endpoint in ro.endpoints:
                fn = self.lambda_builder.build_lambda(endpoint)

                # pass lambda fn to controller
                _controllers[ro.group].add_method(endpoint, fn)
                self.add_method(app, endpoint, lamb_name)

        self.proxy_integrator.load_eme_handlers(_controllers)

        self.p.serv('aws:local_mock:boto3').detach_boto()

    def on_request(self, **kwargs):
        integ = LambdaIntegration()

        resp = integ.run_lambda(**kwargs)
        return integ.parse_response(resp)

    def add_method(self, app: WebsiteApp, endpoint: TomcruEndpointDescriptor, lambda_fn: str):
        # replace AWS APIGW route scheme to flask routing schema
        _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        app._custom_routes[endpoint.endpoint_id].add(_api_route)
