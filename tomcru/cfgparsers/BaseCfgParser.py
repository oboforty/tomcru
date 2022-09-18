import os

from eme.entities import load_settings

from core.cfg import TomcruLambdaIntegrationDescription, TomcruApiAuthorizerDescriptor
from tomcru import TomcruCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor, TomcruApiDescriptor, TomcruApiLambdaAuthorizerDescriptor


class BaseCfgParser:
    def __init__(self, project, name):
        self.proj = project
        self.name = name
        self.cfg: TomcruCfg = None

    def create_cfg(self, path: str, pck_path):
        self.cfg = TomcruCfg(path, pck_path)

        self.parse_project_apis()

    def parse_project_apis(self):
        """
        Parses api configuration in
        :return:
        """

        path = f'{self.cfg.app_path}/cfg/apis'
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('routes.ini'):
                    # eme routing file
                    self.add_eme_routes(os.path.join(path, file), 'http')
                elif file.endswith('.ini'):
                    # tomcru api config file
                    self.add_api_cfg(os.path.join(path, file))
                elif file.endswith('.yaml') or file.endswith('.yml'):
                    # swagger file
                    pass

    def add_api_cfg(self, file):
        r = load_settings(file, delimiters=('=',)).conf

        authorizers = r.pop('authorizers', {})
        # list authorizers
        for auth_id, integ_opt in authorizers.items():
            auth_integ = self.get_auth_integ(auth_id, integ_opt)

            self.cfg.authorizers[auth_id] = auth_integ

        cfg_all_ = r.pop('__default__', {})

        # list lambdas
        for api_name, cfg in r.items():
            cfg = cfg_all_.copy().update(cfg)

            _api_type = cfg.get('type', 'http')
            cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))

            print(f"Processing api: {api_name}")

            # map ini to tomcru descriptor
            cfg_api_.swagger_enabled = cfg.get('swagger_enabled', False)
            cfg_api_.swagger_ui = cfg.get('swagger_ui', False)
            cfg_api_.default_authorizer = cfg.get('default_authorizer', None)

    def add_eme_routes(self, file, integration, check_files=False):
        assert integration is not None

        r = load_settings(file, delimiters=('=>', '->')).conf

        # list lambdas
        for api_name, api in r.items():

            _api_type = integration
            if _api_type == 'rest':
                raise Exception("HTTPv1 not supported")

            cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))

            print(f"Processing routes: {api_name}")
            for endpoint, *integ_opts in api.items():
                if endpoint.startswith('#'):
                    # ignore comments
                    continue

                method, route = endpoint.split(' ')

                endpoint_integ = self.get_integ(integ_opts, check_files, group, route, method)

                # add Api Gateway integration
                cfg_api_.routes.setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                cfg_api_.routes[route].add_endpoint(endpoint_integ)

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

    def get_integ(self, integ_opts, check_files: bool, group, route, method) -> TomcruEndpointDescriptor:
        """

        :param integ_opts:
        :param check_files:
        :param group:
        :param route:
        :param method:
        :return:
        """
        integ_type, integ_id = integ_opts[0].split(':')

        if 'lambda' == integ_type or 'l' == integ_type:
            auth = next(filter(lambda x: x.startswith('auth:'), integ_opts), None)
            role = next(filter(lambda x: x.startswith('role:'), integ_opts), 'LambdaExecRole')
            layers = next(filter(lambda x: x.startswith('layers:'), integ_opts), [])
            # Lambda integration
            integ = TomcruLambdaIntegrationDescription(group, route, method, integ_id, layers, role, auth)

            if check_files:
                # check if files exist
                if not os.path.exists(f'{self.cfg.app_path}/lambdas/{group}/{integ_id}'):
                    print("ERR: Lambda folder", group, integ_id, 'does not exist!')
                    #continue
                    return None
        else:
            raise Exception(f"Integration {integ_type} not recognized!")

        return integ
        # if len(grrr) == 4:
        #     lamb, layers, role = grrr
        # else:
        # lamb, layers = grrr


        layers = layers.split("|")
        if layers[0] == '':
            layers = layers.pop(0)
        self.cfg.lambdas.add((group, lamb, tuple(layers)))

    def get_auth_integ(self, auth_id, integ_opt) -> TomcruApiAuthorizerDescriptor:
        auth_type, integ_opt = integ_opt.split(':')

        if 'lambda' == auth_type or 'l' == auth_type:
            lambda_source, lambda_id = integ_opt.split('/')

            return TomcruApiLambdaAuthorizerDescriptor(auth_id, lambda_id, lambda_source)
        else:
            pass
