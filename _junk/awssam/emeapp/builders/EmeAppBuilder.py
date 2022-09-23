from eme.entities import load_config
from awssam.AwsSamCfg import AwsSamCfg, AwsSamRouteDescriptor, AwsSamEndpointDescriptor

from . import lib_replacer, start_flask_app
from .LambdaBuilder import LambdaBuilder
from .HttpProxyContextBuilder import HttpProxyContextBuilder
from .WsProxyContextBuilder import WsProxyContextBuilder

from ..services import LocalDevAuthorizerServer, EmeProxyController


class EmeAppBuilder:
    def __init__(self, cfg: AwsSamCfg):
        self.cfg = cfg
        self.opts = load_config(self.cfg.app_path + '/sam/emecfg/apigw.ini')
        if self.opts is None:
            self.opts = {}

        self.lambda_builder = LambdaBuilder(self.cfg)
        self.auth_server = LocalDevAuthorizerServer()

        # eme app dependent logic
        self.proxy_integrator = None

    def build_app(self, env, app_type = None):
        _is_ws = app_type == 'ws'

        if not _is_ws:
            # Api GW HTTP2 integration:
            self.proxy_integrator = HttpProxyContextBuilder(self.cfg)
        else:
            self.proxy_integrator = WsProxyContextBuilder(self.cfg)

        app = self.proxy_integrator.app


        # propagate cfg to boto3 & inject eme mock lib
        b3 = lib_replacer.install(app, self.cfg.app_path, self.cfg.layers)
        self._build_authorizers(env)
        self._build_controllers()
        lib_replacer.uninstall()
        app.boto3 = b3

        # return built app
        return app

    def _build_controllers(self):
        _controllers = {}

        for api_name, routes in self.proxy_integrator.route_collections:
            # write endpoints to lambda + integrations
            ro: AwsSamRouteDescriptor
            for route, ro in routes.items():
                if ro.group not in _controllers:
                    _controllers[ro.group] = EmeProxyController(ro.group, self.proxy_integrator, self.lambda_builder)

                endpoint: AwsSamEndpointDescriptor
                for endpoint in ro.endpoints:
                    fn = self.lambda_builder.build_lambda(endpoint)

                    # pass lambda fn to controller
                    _controllers[ro.group].add_method(endpoint, fn)

        self.proxy_integrator.load_eme_handlers(_controllers)

    def _build_authorizers(self, env):
        # build HTTP authorizer
        fcfg = self.opts['faas']

        if fcfg['authorizer_enabled'] == 'yes' or fcfg['authorizer_enabled'] == True:
            self.proxy_integrator.set_authorizer(fcfg['authorizer'], self.lambda_builder.build_lambda(fcfg['authorizer']))
        elif fcfg:
            self.proxy_integrator.mock_authorizer(fcfg['authorizer_mock'])

    def run_lambda(self, lambda_name, inputs: dict, env: str = None, app_type=None, mocked_authorizer=None):
        _is_ws = app_type == 'ws'

        if not _is_ws:
            # Api GW HTTP2 integration:
            self.proxy_integrator = HttpProxyContextBuilder(self.cfg)
        else:
            self.proxy_integrator = WsProxyContextBuilder(self.cfg)

        app = self.proxy_integrator.app

        _cont = EmeProxyController('InstancedLambdaRunner', self.proxy_integrator, self.lambda_builder)

        # propagate cfg to boto3 & inject eme mock lib
        _layers_paths = map(lambda f: f[3], self.cfg.layers)
        _layers_keywords = map(lambda f: f[1][0], self.cfg.layers)
        b3 = lib_replacer.install(app, self.cfg.app_path, _layers_paths, _layers_keywords)
        if mocked_authorizer:
            self.proxy_integrator.mock_authorizer(mocked_authorizer)
        fn = self.lambda_builder.build_lambda(lambda_name)
        _cont.methods['asd'] = fn
        lib_replacer.uninstall()
        app.boto3 = b3

        return _cont.general_method(**inputs)

    def start_auth_dev_server(self):
        if self.auth_server:
            _envvars = self.cfg.envs.get('LocalAuthDevServer')

            if _envvars and _envvars['enabled']:
                print("Starting local dev authorizer server")
                start_flask_app.start_flask_app("Lambda authorizer", self.auth_server.mock_server_builder, _envvars['host'])

    def start_app_threaded(self, name, builder, host):
        start_flask_app.start_flask_app(name, builder, host)
