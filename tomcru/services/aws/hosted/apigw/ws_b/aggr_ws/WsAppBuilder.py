from tomcru import TomcruApiDescriptor, TomcruProject, TomcruRouteDescriptor, TomcruLambdaIntegrationDescription

from .apps.EmeWsApp import EmeWsApp

from tomcru.services.aws.onpremise.aggr_api.ApiGwBuilderCore import ApiGwBuilderCore
from .integration.LambdaIntegration import LambdaIntegration
from .integration.WsEnRouteCachedAuthorizer import WsEnRouteCachedAuthorizer


class WsAppBuilder(ApiGwBuilderCore):
    WS_METHOD_PARAMS = ['route', 'msid', 'user', 'data', 'client', 'token']

    def __init__(self, project: TomcruProject, apigw_cfg):
        super().__init__(project, apigw_cfg)

        #self.api_serv = self.p.serv('aws:onpremise:aggr_api')

    def init(self):
        pass

    def build_api(self, api_name, api: TomcruApiDescriptor, env: str):
        self.env = env

        # build eme app object
        apiopts = self.apigw_cfg.get('__default__', {})
        apiopts.update(self.apigw_cfg.get(api_name, {}))

        self.app = EmeWsApp(self.cfg.apis[api_name], apiopts)
        self.mgr.add_app(self.app)

        self._build_authorizers()
        self._build_groups(api)

        return self.app

    def _build_groups(self, api):
        _connect_authorizer = None

        # find base authorizer (for connect)
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():

            endpoint: TomcruLambdaIntegrationDescription
            for endpoint in ro.endpoints:
                if endpoint.route == "$connect":
                    _connect_authorizer = self.authorizers[endpoint.auth] if endpoint.auth else api.default_authorizer
                    break
            else:
                continue
            break # break when inner loop breaks :v

        _integ_authorizer = WsEnRouteCachedAuthorizer(_connect_authorizer)

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():

            endpoint: TomcruLambdaIntegrationDescription
            for endpoint in ro.endpoints:
                # if endpoint.route == "$connect":

                if isinstance(endpoint, TomcruLambdaIntegrationDescription):
                    # build lambda integration
                    _integration = LambdaIntegration(self.app, endpoint, _integ_authorizer, self.p.serv('aws:onpremise:lambda_b'), env=self.env)
                else:
                    # todo: for now we assume it's always lambda
                    raise NotImplementedError()

                # refer to integration (proxy controller refers to self.on_request)
                #self.integrations[endpoint] = _integration

                self.add_method(endpoint, _integration)
        self.app.debug_groups({})

    def add_method(self, endpoint, _integration):
        # todo: later: do not use endpoint_id for lambda id!
        _horrible_unique_id = endpoint.endpoint+'>'+endpoint.endpoint_id

        self.app._methods[_horrible_unique_id] = (_integration.on_request, self.WS_METHOD_PARAMS)
        self.app._endpoints_to_methods[endpoint.endpoint] = _horrible_unique_id
