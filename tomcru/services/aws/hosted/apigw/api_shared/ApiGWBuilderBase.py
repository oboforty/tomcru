import os.path

from abc import ABCMeta, abstractmethod

from services.aws.hosted.apigw.api_shared.integration import TomcruApiGWHttpIntegration
from tomcru.services.ServiceBase import ServiceBase
from tomcru import TomcruApiDescriptor, TomcruEndpointDescriptor, TomcruRouteDescriptor, TomcruLambdaIntegrationDescription, TomcruSwaggerIntegrationDescription, TomcruMockedIntegrationDescription


__dir__ = os.path.dirname(os.path.realpath(__file__))


class ApiGWBuilderBase(ServiceBase, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.authorizers: dict[str, str] = {}
        self.integrations: dict[TomcruEndpointDescriptor, TomcruApiGWHttpIntegration] = {}
        self.port2app: dict[int, str] = {}

        self.apps: dict[str, object] = {}

    def init(self):

        # build apis here
        for api_name, api in self.p.cfg.apis.items():
            apiopts = { **self.opts.get('default', {}), **self.opts.get(f'apis.{api_name}', {}) }

            self.apps[api.api_name] = self.create_app(api, apiopts)

            conn_id = api_name
            self.service('apigw_manager').add_app(self, conn_id)

            self._build_authorizers()
            index = self._build_integrations(api, apiopts)

            self.add_extra_route_handlers(api, index)

            self.port2app[apiopts['port']] = api_name

    def _build_authorizers(self):
        #self.p.cfg.authorizers
        pass

    def _build_integrations(self, api, apiopts) -> TomcruEndpointDescriptor | None:
        #swagger_converter = self.service('')

        # build controllers
        _index = None
        _swagger: dict[str, TomcruSwaggerIntegrationDescription | None] = {"json": None, "html": None, "yaml": None}
        api_root = apiopts.get('api_root', '')

        # write endpoints to lambda + integrations
        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():
            endpoint: TomcruEndpointDescriptor
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None

                # refer to integration (proxy controller refers to self.on_request)
                _integration: TomcruApiGWHttpIntegration = self.get_integration(api, endpoint, auth)

                if _integration is None:
                    print(f"Not found integration for {endpoint}")
                    continue
                self.integrations[endpoint] = _integration
                self.add_method(api, ro, endpoint, apiopts, _integration)

                if endpoint.route == '/':
                    _index = endpoint

        # create swagger UI (both ui and json endpoints are needed)
        # if api.swagger_enabled and api.swagger_ui and _swagger and all(_swagger.values()):
        #     # todo: integrate with yaml too? can this be decided? does swagger UI allow even?
        #     integrate_swagger_ui_blueprint(self.app, _swagger['json'], _swagger['html'])

        return _index

    def get_app(self, api_name):
        return self.apps[api_name], self.opts.get(f'apis.{api_name}', {})

    def on_request(self, **kwargs):
        ep, api = self.get_called_endpoint(**kwargs)
        integ = self.integrations[ep]

        response = integ.on_request(**kwargs)

        if api.swagger_check_models and api.spec_resolved_schemas:
            # todo: make swagger model checker work
            pass
            # try:
            #     self.service()
            #     self.p.serv("aws:onpremise:model_checker").check_response(api, ep, response, env=self.env)
            # except Exception as e:
            #     if self.env == 'dev' or self.env == 'debug':
            #         raise e
            #     else:
            #         print("!! Swagger model checker raised an exception: ", str(e))

        return self.parse_response(response)

    @abstractmethod
    def parse_response(self, response):
        pass
    @abstractmethod
    def create_app(self, api: TomcruApiDescriptor, opts: dict):
        return None

    @abstractmethod
    def add_method(self, api: TomcruApiDescriptor, route: TomcruRouteDescriptor, endpoint: TomcruEndpointDescriptor, opts: dict, _integration: TomcruApiGWHttpIntegration):
        pass

    @abstractmethod
    def add_extra_route_handlers(self, api: TomcruApiDescriptor, index: TomcruEndpointDescriptor | None = None):
        pass

    @abstractmethod
    def get_called_endpoint(self, **kwargs) -> tuple[TomcruEndpointDescriptor, TomcruApiDescriptor]:
        pass

    @abstractmethod
    def get_integration(self, api: TomcruApiDescriptor, endpoint: TomcruEndpointDescriptor):
        pass
