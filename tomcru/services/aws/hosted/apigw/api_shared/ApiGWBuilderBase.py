import logging
import os.path

from abc import ABCMeta, abstractmethod

from tomcru.services.ServiceBase import ServiceBase
from tomcru import TomcruApiEP, TomcruEndpoint, TomcruRouteEP, TomcruSwaggerIntegrationEP, TomcruApiLambdaAuthorizerEP, TomcruApiOIDCAuthorizerEP
from .integration import TomcruApiGWHttpIntegration, TomcruApiGWAuthorizerIntegration, LambdaAuthorizerIntegration, ExternalLambdaAuthorizerIntegration, OIDCAuthorizerIntegration

__dir__ = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('tomcru')


class ApiGWBuilderBase(ServiceBase, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.authorizers: dict[str, str] = {}
        self.integrations: dict[TomcruEndpoint, TomcruApiGWHttpIntegration] = {}
        self.port2app: dict[int, str] = {}

        self.apps: dict[str, object] = {}

    def get_app(self, api_name):
        if api_name not in self.apps:

            raise Exception(f"Api {api_name} not found! Available apis: {', '.join(self.apps.keys())}")
        return self.apps[api_name], self.opts.get(f'apis.{api_name}', {})

    def inject_dependencies(self):
        # inject deps is called before init, first create all app objects
        # so that apps with attach_to can be injected into already existing ones in init

        for api_name, api in self.p.cfg.apis.items():
            apiopts = { **self.opts.get('default', {}), **self.opts.get(f'apis.{api_name}', {}) }

            if 'attach_to' in apiopts:
                # skip building api if it's configured to be attached to another app+port
                continue

            self.apps[api.api_name] = self.create_app(api, apiopts)

    def init(self):
        # build apis here
        for api_name, api in self.p.cfg.apis.items():
            apiopts = { **self.opts.get('default', {}), **self.opts.get(f'apis.{api_name}', {}) }

            if 'attach_to' in apiopts:
                # attach this api to an already existing app
                serv_id = apiopts['attach_to']['service']
                api_name = apiopts['attach_to']['app']

                try:
                    parent_app, parent_opts = self.service(serv_id).get_app(api_name)
                except:
                    raise Exception(f"Referenced app not found in attach_to: {serv_id}->{api_name}")
                self.apps[api.api_name] = parent_app

            self._build_app(api, apiopts)

    def _build_app(self, api: TomcruApiEP, apiopts: dict):
        conn_id = api.api_name
        self.service('apigw_manager').add_app(self, conn_id)

        self._build_authorizers()
        self.build_acl(api, apiopts.get('cors'))
        index = self._build_integrations(api, apiopts)

        self.add_extra_route_handlers(api, index)

        self.port2app[apiopts['port']] = api.api_name

    def _build_authorizers(self):
        authorizers = self.p.cfg.authorizers
        self.authorizers: dict[str, TomcruApiGWAuthorizerIntegration] = {}

        # build authorizers
        for authorizer_id, auth in authorizers.items():
            if isinstance(auth, TomcruApiLambdaAuthorizerEP):
                # evaluate lambda sub type
                if 'external' == auth.lambda_source:
                    raise NotImplementedError("__fileloc__")
                    self.authorizers[authorizer_id] = ExternalLambdaAuthorizerIntegration(auth, self.opts)
                else:
                    self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.opts, self.service('lambda'), env=self.env)

            elif isinstance(auth, TomcruApiOIDCAuthorizerEP):
                self.authorizers[authorizer_id] = OIDCAuthorizerIntegration(auth, self.opts, env=self.env)
            else:
                # todo: implement IAM and jwt
                raise NotImplementedError(authorizer_id)

        return self.authorizers


    def _build_integrations(self, api, apiopts) -> TomcruEndpoint | None:
        #swagger_converter = self.service('')

        # build controllers
        _index = None
        _swagger: dict[str, TomcruSwaggerIntegrationEP | None] = {"json": None, "html": None, "yaml": None}
        api_root = apiopts.get('api_root', '')

        # write endpoints to lambda + integrations
        ro: TomcruRouteEP
        for route, ro in api.routes.items():
            endpoint: TomcruEndpoint
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None

                # refer to integration (proxy controller refers to self.on_request)
                _integration: TomcruApiGWHttpIntegration = self.get_integration(api, endpoint, auth)

                if _integration is None:
                    logger.warning(f"Not found integration for {endpoint}")
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

    def on_request(self, **kwargs):
        ep, api = self.get_called_endpoint(**kwargs)

        integ = self.integrations[ep]

        base_headers = {
            **self.opts.get('default.headers', {}),
            **self.opts.get(f'apis.{api.api_name}.headers', {})
        }
        response = integ.on_request(base_headers=base_headers, **kwargs)

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
    def create_app(self, api: TomcruApiEP, opts: dict):
        return None

    @abstractmethod
    def add_method(self, api: TomcruApiEP, route: TomcruRouteEP, endpoint: TomcruEndpoint, opts: dict, _integration: TomcruApiGWHttpIntegration):
        pass

    @abstractmethod
    def build_acl(self, api: TomcruApiEP, acl: dict):
        pass

    @abstractmethod
    def add_extra_route_handlers(self, api: TomcruApiEP, index: TomcruEndpoint | None = None):
        pass

    @abstractmethod
    def get_called_endpoint(self, **kwargs) -> tuple[TomcruEndpoint, TomcruApiEP]:
        pass

    @abstractmethod
    def get_integration(self, api: TomcruApiEP, endpoint: TomcruEndpoint):
        pass
