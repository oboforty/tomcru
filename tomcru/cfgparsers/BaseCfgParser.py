import os

from tomcru.core import TomcruCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor


class BaseCfgParser:
    def __init__(self, project, name):
        self.proj = project
        self.name = name
        self.cfg = None

    def create_cfg(self, path: str):
        self.cfg = TomcruCfg(path)

    def add_eme_routes(self, api_name, integration=None, check_files=False):
        from eme.entities import load_settings

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
                    _cont = self.cfg.apis
                elif integration == 'ws':
                    _cont = self.cfg.wss
                elif integration == 'rest':
                    raise Exception("HTTPv1 not supported")
                else:
                    # else: no integration
                    return

                # add Api Gateway integration
                ep = TomcruEndpointDescriptor(group, route, method, lamb, role, layers)
                _cont[api_name].setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                _cont[api_name][route].add_endpoint(ep)

    def add_openapi_routes(self, api_name, integration=None, check_files=False):
        from openapi_parser import parse

        file = os.path.join(self.cfg.app_path, 'routes', api_name+'.yml')
        if not os.path.exists(file): file = file[:-4] + '.yaml'
        if not os.path.exists(file): raise Exception("File doesnt exist: " + file)
        specification = parse(file)

        for path in specification.paths:
            group = path.url.replace('/', '_').strip('_')
            route = path.url

            for op in path.operations:
                method = op.method.name

                ep = TomcruEndpointDescriptor(group, route, method, lamb, role, layers)
                self.cfg.apis[api_name].setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                self.cfg.apis[api_name][route].add_endpoint(ep)

    def add_layer(self, layer_name, files=None, packages=None, folder=None, single_file=False, in_house=True):
        self.cfg.layers.append((layer_name, files, packages, folder, single_file, in_house))

    def load_envs(self, env):
        self.cfg.envs = dict(load_settings(self.cfg.app_path+'/sam/cfg/'+env+'/envlist.ini').conf)
