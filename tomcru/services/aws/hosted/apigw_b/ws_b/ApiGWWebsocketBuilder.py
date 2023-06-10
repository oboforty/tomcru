import json
import os.path

from tomcru import TomcruApiEP, TomcruEndpoint, TomcruRouteEP, TomcruLambdaIntegrationEP

__dir__ = os.path.dirname(os.path.realpath(__file__))

from tomcru.services.aws.hosted.apigw_b.api_shared.ApiGWBuilderBase import ApiGWBuilderBase

from .wsapp.websocket import WebsocketApp
from .integration import LambdaIntegration, WsEnRouteCachedAuthorizer


class ApiGWWebsocketBuilder(ApiGWBuilderBase):
    INIT_PRIORITY = 5
    WS_METHOD_PARAMS = ['route', 'msid', 'user', 'data', 'client', 'token']

    def __init__(self, *args, **kwargs):
        self.apps: dict[str, WebsocketApp] = {}

        super().__init__(*args, **kwargs)

    def create_app(self, api: TomcruApiEP, apiopts: dict):
        port = apiopts.get('port', 5000)

        api_id = f'{api.api_name}:{port}'
        app = WebsocketApp({
            'host': '0.0.0.0',
            'port': port,
        })

        # set custom attributes
        app.api_name = api_id
        app.api_type = 'ws'
        app.is_main_thread = apiopts.get('main_api', False)

        # create authorizer for new connections
        _connect_authorizer = None

        # find base authorizer (for connect)
        ro: TomcruRouteEP
        for route, ro in api.routes.items():

            endpoint: TomcruLambdaIntegrationEP
            for endpoint in ro.endpoints:
                if endpoint.route == "$connect":
                    _connect_authorizer = self.authorizers[endpoint.auth] if endpoint.auth else api.default_authorizer
                    break
            else:
                continue
            # break when inner loop breaks :v
            break

        app._integ_authorizer = WsEnRouteCachedAuthorizer(_connect_authorizer)

        return app

    def get_called_endpoint(self, **kwargs) -> tuple[TomcruEndpoint, TomcruApiEP]:
        raise NotImplementedError("Not needed")

    def add_method(self, api: TomcruApiEP, route: TomcruRouteEP, endpoint: TomcruEndpoint, apiopts: dict, _integration: object):
        # replace AWS APIGW route scheme to flask routing schema
        app: WebsocketApp = self.get_app(api.api_name)

        _horrible_unique_id = endpoint.endpoint+'>'+endpoint.endpoint_id

        app._methods[_horrible_unique_id] = (_integration, self.WS_METHOD_PARAMS)
        app._endpoints_to_methods[endpoint.endpoint] = _horrible_unique_id

    def add_extra_route_handlers(self, api: TomcruApiEP, index: TomcruEndpoint | None = None):
        pass

    def parse_response(self, response):
        return response

    def get_integration(self, api: TomcruApiEP, endpoint: TomcruEndpoint, auth):
        app = self.get_app(api.api_name)

        if isinstance(endpoint, TomcruLambdaIntegrationEP):
            # build lambda integration
            _integration = LambdaIntegration(endpoint, app._integ_authorizer, self.service('lambda'), env=self.env)
        else:
            raise NotImplementedError(type(endpoint))

        return _integration

    def build_acl(self, api: TomcruApiEP, acl: dict):
        pass
