import json
import os.path
import re
import logging
from typing import Callable

from tomcru import \
    TomcruApiEP, TomcruEndpoint, TomcruRouteEP, \
    TomcruLambdaIntegrationEP
from tomcru.services.aws.hosted.apigw_b.ApiGWSubserviceBase import ApiGWSubserviceBase
from .integration import \
    LambdaIntegration, WsEnRouteCachedAuthorizer

from .wsapp.websocket import WebsocketApp


__dir__ = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('tomcru')


class ApiGWWebsocketsSubservice(ApiGWSubserviceBase):
    # transforms greedy path rules between AWS and Flask
    rgx_greedy_path_a2f = re.compile(r'\{([\w\d_]*)\+\}')
    rgx_greedy_path_f2a = re.compile(r'<path:([\w\d_]*)>')

    WS_METHOD_PARAMS = ['route', 'msid', 'user', 'data', 'client', 'token']

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

        return app

    def build_api(self, api: TomcruApiEP, apiopts: dict):
        conn_id = api.api_name
        self.service('apigw_manager').add_app(self, conn_id)

        self._build_authorizers(api, apiopts)
        self._build_integrations(api, apiopts)

    def _build_authorizers(self, api: TomcruApiEP, apiopts: dict):
        app: WebsocketApp = self.parent.apps[api.api_name]
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

    def _build_integrations(self, api: TomcruApiEP, apiopts: dict):
        app: WebsocketApp = self.parent.apps[api.api_name]
        logger.debug(f"[apigw] {api.api_name} Building integrations for {len(api.routes)} routes")

        # write endpoints to lambda + integrations
        ro: TomcruRouteEP
        for route, ro in api.routes.items():

            endpoint: TomcruEndpoint
            for endpoint in ro.endpoints:
                # refer to integration (proxy controller refers to self.on_request)
                _integration: Callable = self._build_integration_to_endpoint(app, api, endpoint)

                if _integration is None:
                    logger.warning(f"[apigw] Not found integration for {endpoint}")
                    continue
                self.integrations[endpoint] = _integration

                # add ws method
                _horrible_unique_id = endpoint.endpoint+'>'+endpoint.endpoint_id
                app._methods[_horrible_unique_id] = (_integration, self.WS_METHOD_PARAMS) # noqa
                app._endpoints_to_methods[endpoint.endpoint] = _horrible_unique_id # noqa

    def _build_integration_to_endpoint(self, app, api, endpoint):
        _integration: Callable

        if isinstance(endpoint, TomcruLambdaIntegrationEP):
            # build lambda integration
            _integration = LambdaIntegration(app, endpoint, self.service('lambda'))
        #elif isinstance(endpoint, TomcruMockedIntegrationEP):
        else:
            raise NotImplementedError(type(endpoint))

        return _integration

    def print_endpoints(self, app, apiopts):
        print("@TODO: print WS endpoints")
        pass
