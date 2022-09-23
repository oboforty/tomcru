import os

from .AwsSamCfg import AwsSamCfg, AwsSamRouteDescriptor, AwsSamEndpointDescriptor
from .samapp import SamTplBuilder
from .emeapp import EmeAppBuilder
from eme.entities import load_settings


class AwsSamProjectBuilder:
    def __init__(self, path: str):
        self.cfg = AwsSamCfg(path)

        self._b_sam = SamTplBuilder(self.cfg)
        self._b_eme = EmeAppBuilder(self.cfg)

    def add_routes(self, api_name, integration=None, check_files=False):
        file = f'{self.cfg.app_path}/routes/{api_name}.ini'
        r = load_settings(file, delimiters=('=',)).conf

        # list lambdas
        for group, api in r.items():

            print("Processing " + group)
            for endpoint, (lamb, layers) in api.items():
                # if len(grrr) == 4:
                #     lamb, layers, role = grrr
                # else:
                # lamb, layers = grrr
                role = 'LambdaExecRole'

                if endpoint.startswith('#'):
                    # ignore comments
                    continue

                method, route = endpoint.split(' ')

                if check_files:
                    # check if files exist
                    if not os.path.exists(f'{self.cfg.app_path}/lambdas/{group}/{lamb}'):
                        print("ERR: Lambda folder", group, lamb, 'does not exist!')
                        continue

                layers = layers.split("|")
                if layers[0] == '':
                    layers = layers.pop(0)
                self.cfg.lambdas.add((group, lamb, tuple(layers)))

                _api = None
                if integration == 'http':
                    ep = AwsSamEndpointDescriptor(group, route, method, lamb, role, layers)

                    # add Api Gateway HTTP2 integration
                    self.cfg.apis[api_name].setdefault(route, AwsSamRouteDescriptor(route, group, api_name))
                    self.cfg.apis[api_name][route].add_endpoint(ep)
                elif integration == 'ws':
                    ep = AwsSamEndpointDescriptor(group, route, method, lamb, role, layers)

                    # add Api Gateway websocket integration
                    self.cfg.wss[api_name].setdefault(route, AwsSamRouteDescriptor(route, group, api_name))
                    self.cfg.wss[api_name][route].add_endpoint(ep)
                elif integration == 'rest':
                    raise Exception("HTTPv1 not supported")
                # else: no integration


    def add_layer(self, layer_name, files=None, packages=None, folder=None, single_file=False, in_house=True):
        self.cfg.layers.append((layer_name, files, packages, folder, single_file, in_house))

    def build_template(self, _env, name='template.yaml'):
        self.load_envs(_env)

        self._b_sam.build_template(_env, name)

    def build_layers(self):
        self._b_sam.build_layers()

    def build_eme_app(self, _env, app_type):
        self.load_envs(_env)

        return self._b_eme.build_app(_env, app_type)

    def run_server(self, env, app_type, port=5000, threaded=False):
        if app_type == 'auth':
            if env != 'debug' and env != 'dev':
                print(f"Warning: env is set to {env}, but auth dev server is being run!")
            self._b_eme.start_auth_dev_server()
        else:
            def __builder():
                app = self.build_eme_app(env, app_type)
                app.port = port

                return app

            if threaded:
                self._b_eme.start_app_threaded(app_type + " server", __builder, ':'.join(app.host, app.port))
            else:
                app = __builder()
                app.start()

    def load_envs(self, env):
        self.cfg.envs = dict(load_settings(self.cfg.app_path+'/sam/cfg/'+env+'/envlist.ini').conf)
