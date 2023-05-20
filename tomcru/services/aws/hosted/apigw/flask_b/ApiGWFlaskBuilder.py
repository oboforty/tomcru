import json
import os.path
import re

from flask import request, Flask

from tomcru.services.aws.hosted.apigw.api_shared.integration import TomcruApiGWHttpIntegration
from .integration import SwaggerIntegration, LambdaIntegration, MockedIntegration

from tomcru import TomcruApiEP, TomcruEndpoint, TomcruRouteEP, TomcruLambdaIntegrationEP, TomcruSwaggerIntegrationEP, TomcruMockedIntegrationEP, TomcruApiAuthorizerEP
from tomcru_jerry.controllers import add_endpoint

__dir__ = os.path.dirname(os.path.realpath(__file__))

from tomcru.services.aws.hosted.apigw.api_shared.ApiGWBuilderBase import ApiGWBuilderBase
from tomcru.services.aws.hosted.apigw.api_shared.integration.FlaskCorsAfterRequestHook import FlaskCorsAfterRequestHook


class ApiGWFlaskBuilder(ApiGWBuilderBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        self.apps: dict[str, Flask] = {}

        super().__init__(*args, **kwargs)

        # transforms greedy path rules between AWS and Flask
        self.rgx_greedy_path_a2f = re.compile(r'\{([\w\d_]*)\+\}')
        self.rgx_greedy_path_f2a = re.compile(r'<path:([\w\d_]*)>')

    def init(self):
        super().init()

    def create_app(self, api: TomcruApiEP, apiopts: dict):
        port = apiopts.get('port', 5000)

        api_id = f'{api.api_name}:{port}'
        app = Flask(api_id)

        # set custom attributes
        app.api_name = api_id
        app.api_type = 'http'
        app.is_main_thread = apiopts.get('main_api', False)

        return app

    def get_called_endpoint(self, **kwargs) -> tuple[TomcruEndpoint, TomcruApiEP]:
        # find api name by port
        port = int(request.server[1])#request.host.split(':')[1] if ':' in request.host else 80
        api_name = self.port2app.get(port) #cached store

        if not api_name:
            # api_name = next(filter(lambda a: int(self.apps[a].name.split(':')[1]) == port, self.apps), None)
            # look up api
            for aname, app in self.apps.items():
                _rules = set(map(str, app.url_map._rules))
                if str(request.url_rule) in _rules:
                    api_name = aname
                    break
            else:
                raise Exception("Couldn't find api by port " + str(port))

            # cache expensive lookup
            self.port2app[port] = api_name

        api = self.p.cfg.apis[api_name]
        api_root = self.opts.get(f'apis.{api.api_name}.api_root', '')

        # find route by flask request route
        aws_route_key = str(request.url_rule)
        aws_route_key = self.rgx_greedy_path_f2a.sub(r'{\1+}', aws_route_key)
        aws_route_key = aws_route_key.replace('<', '{').replace('>', '}').removeprefix(api_root)

        route = api.routes[aws_route_key]
        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        return endpoint, api

    def add_method(self, api: TomcruApiEP, route: TomcruRouteEP, endpoint: TomcruEndpoint, apiopts: dict, _integration: object):
        # replace AWS APIGW route scheme to flask routing schema
        api_root = apiopts.get('api_root', '')

        flask_route_key = endpoint.route
        flask_route_key = self.rgx_greedy_path_a2f.sub(r'<path:\1>', flask_route_key)
        flask_route_key = flask_route_key.replace('{', '<').replace('}', '>')

        _api_route = f'{endpoint.method.upper()} {api_root}{flask_route_key}'

        add_endpoint(self.apps[api.api_name], _api_route, endpoint.endpoint_id, self.on_request)

    def add_extra_route_handlers(self, api: TomcruApiEP, index: TomcruEndpoint | None = None):
        pass

    def parse_response(self, response):
        return response

    def get_integration(self, api: TomcruApiEP, endpoint: TomcruEndpoint, auth):

        _integration: TomcruApiGWHttpIntegration

        if isinstance(endpoint, TomcruLambdaIntegrationEP):
            # build lambda integration
            _integration = LambdaIntegration(endpoint, auth, self.service('lambda'), env=self.env)
        elif isinstance(endpoint, TomcruSwaggerIntegrationEP):
            return None
            # todo: add support for swagger EP
            # _swagger[endpoint.req_content] = endpoint
            #
            # if endpoint.req_content != 'html':
            #     _integration = SwaggerIntegration(api, endpoint, swagger_converter, env=self.env)
            # else:
            #     continue
        elif isinstance(endpoint, TomcruMockedIntegrationEP):
            if endpoint.file:
                filepath = os.path.join(self.env.spec_path, endpoint.file)

                with open(filepath) as fh:
                    response = json.load(fh)
            else:
                # resolve by swagger examples
                raise NotImplementedError("OpenApi: Examples mock")

            _integration = MockedIntegration(endpoint, auth, response, env=self.env)
        else:
            raise NotImplementedError(type(endpoint))

        return _integration

    def build_acl(self, api: TomcruApiEP, acl: dict):
        if acl is None:
            return

        app: Flask = self.apps[api.api_name]

        f = FlaskCorsAfterRequestHook(acl)
        app.after_request(lambda resp: f(request, resp))
