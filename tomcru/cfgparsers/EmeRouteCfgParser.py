import os

from tomcru.core import TomcruCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor
from eme.entities import load_settings


class EmeRouteCfgParser:
    def __init__(self, cfg: TomcruCfg):
        self.cfg = cfg

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
                    ep = TomcruEndpointDescriptor(group, route, method, lamb, role, layers)

                    # add Api Gateway HTTP2 integration
                    self.cfg.apis[api_name].setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                    self.cfg.apis[api_name][route].add_endpoint(ep)
                elif integration == 'ws':
                    ep = TomcruEndpointDescriptor(group, route, method, lamb, role, layers)

                    # add Api Gateway websocket integration
                    self.cfg.wss[api_name].setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                    self.cfg.wss[api_name][route].add_endpoint(ep)
                elif integration == 'rest':
                    raise Exception("HTTPv1 not supported")
                # else: no integration
