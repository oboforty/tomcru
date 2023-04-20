import os.path

from flask import request, Flask

from services.aws.hosted.apigw.api_shared.integration import TomcruApiGWHttpIntegration
from .integration import SwaggerIntegration, LambdaIntegration, MockedIntegration

from tomcru import TomcruApiDescriptor, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruLambdaIntegrationDescription, TomcruSwaggerIntegrationDescription, TomcruMockedIntegrationDescription, TomcruApiAuthorizerDescriptor
from tomcru_jerry import flask_jerry_setup
from tomcru_jerry.controllers import add_endpoint

__dir__ = os.path.dirname(os.path.realpath(__file__))

from tomcru.services.aws.hosted.apigw.api_shared.ApiGWBuilderBase import ApiGWBuilderBase


class ApiGWFlaskBuilder(ApiGWBuilderBase):

    def __init__(self, *args, **kwargs):
        self.apps: dict[str, Flask] = {}

        super().__init__(*args, **kwargs)

    def init(self):
        super().init()

    def create_app(self, api: TomcruApiDescriptor, apiopts: dict):
        port = apiopts.get('port', 5000)

        api_id = f'{api.api_name}:{port}'
        app = Flask(api_id)

        flask_jerry_setup(app, apiopts)

        # set custom attributes
        app.api_name = api_id
        app.api_type = 'http'
        app.is_main_thread = apiopts.get('main_api', False)

        return app

    def get_called_endpoint(self, **kwargs) -> tuple[TomcruEndpointDescriptor, TomcruApiDescriptor]:
        # find app
        port = request.host.split(':')[1]
        api = self.p.cfg.apis[self.port2app[int(port)]]
        api_root = self.opts.get(f'apis.{api.api_name}.api_root', '')

        # find route by flask request route
        aws_routekey = str(request.url_rule).replace('<', '{').replace('>', '}').removeprefix(api_root)
        route = api.routes[aws_routekey]

        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        return endpoint, api

    def add_method(self, api: TomcruApiDescriptor, route: TomcruRouteDescriptor, endpoint: TomcruEndpointDescriptor, apiopts: dict, _integration: object):
        # replace AWS APIGW route scheme to flask routing schema
        api_root = apiopts.get('api_root', '')

        flask_route = endpoint.route.replace('{', '<').replace('}', '>')
        _api_route = f'{endpoint.method.upper()} {api_root}{flask_route}'

        add_endpoint(self.apps[api.api_name], _api_route, endpoint.endpoint_id, self.on_request)

    def add_extra_route_handlers(self, api: TomcruApiDescriptor, index: TomcruEndpointDescriptor | None = None):
        pass

    def parse_response(self, response):
        return response

    def get_integration(self, api: TomcruApiDescriptor, endpoint: TomcruEndpointDescriptor, auth):

        _integration: TomcruApiGWHttpIntegration

        if isinstance(endpoint, TomcruLambdaIntegrationDescription):
            # build lambda integration
            _integration = LambdaIntegration(endpoint, auth, self.service('lambda'), env=self.env)
        elif isinstance(endpoint, TomcruSwaggerIntegrationDescription):
            return None
            # todo: add support for swagger EP
            # _swagger[endpoint.req_content] = endpoint
            #
            # if endpoint.req_content != 'html':
            #     _integration = SwaggerIntegration(api, endpoint, swagger_converter, env=self.env)
            # else:
            #     continue
        elif isinstance(endpoint, TomcruMockedIntegrationDescription):
            filepath = os.path.join(self.env.spec_path, 'apigw', endpoint.filename)

            _integration = MockedIntegration(endpoint, auth, filepath, env=self.env)
        else:
            raise NotImplementedError(type(endpoint))

        return _integration
