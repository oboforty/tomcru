import os

from eme.entities import load_settings

from tomcru import TomcruCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor, TomcruApiDescriptor, \
    TomcruApiLambdaAuthorizerDescriptor, TomcruLambdaIntegrationDescription, TomcruApiAuthorizerDescriptor, TomcruSwaggerIntegration, TomcruApiOIDCAuthorizerDescriptor


class BaseCfgParser:
    def __init__(self, project, name):
        self.proj = project
        self.name = name
        self.cfg: TomcruCfg | None = None

        self.subparsers = {}

    def create_cfg(self, path: str, pck_path):
        self.cfg = TomcruCfg(path, pck_path)

    def add_parser(self, cfgpid, cfgp):
        if not cfgp.cfg: cfgp.cfg = self.cfg
        self.subparsers[cfgpid] = cfgp

    def build_service(self, srv, **kwargs):
        self.cfg.extra_srv.append((srv, kwargs))

    def parse_project_apis(self):
        """
        Parses api configuration in
        :return:
        """

        path = f'{self.cfg.app_path}/cfg/apis'

        routes = []

        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('routes.ini'):
                    # eme routing file
                    routes.append(os.path.join(path, file))
                elif file.endswith('.ini'):
                    # tomcru api config file
                    self.add_api_cfg(os.path.join(path, file))
                elif file.endswith('.yaml') or file.endswith('.yml'):
                    # swagger file
                    pass

        for routecfg in routes:
            self.add_eme_routes(routecfg, 'http', check_files = True)

    def parse_envvars(self, vendor):
        """
        Parses lambda and other envvars configured
        :return:
        """

        path = f'{self.cfg.app_path}/cfg/{vendor}'

        for env in os.listdir(path):
            envvar_path = os.path.join(path, env, 'envvars')

            if os.path.exists(envvar_path):
                for root, dirs, files in os.walk(envvar_path):
                    for file in files:
                        if file.endswith('.ini'):
                            # envvar file
                            self.add_envvars(os.path.join(envvar_path, file), env, vendor)

    def add_api_cfg(self, file):
        r = load_settings(file, delimiters=('=',)).conf

        authorizers = r.pop('authorizers', {})
        # list authorizers
        for auth_id, integ_opt in authorizers.items():
            auth_integ = self._get_auth_integ(auth_id, integ_opt)

            self.cfg.authorizers[auth_id] = auth_integ

        cfg_all_ = r.pop('__default__', {})

        # list lambdas
        for api_name, cfg in r.items():
            _api_type = cfg.get('type', 'http')
            print(f"Processing api: {api_name}")

            cfg = {**cfg_all_, **cfg}

            #cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))
            cfg_api_ = self.cfg.apis[api_name] = TomcruApiDescriptor(api_name, _api_type)

            # map ini to tomcru descriptor
            cfg_api_.swagger_enabled = cfg.get('swagger_enabled', False)
            cfg_api_.swagger_ui = cfg.get('swagger_ui', False)
            cfg_api_.swagger_check_models = cfg.get('swagger_check_models', False)
            cfg_api_.default_authorizer = cfg.get('default_authorizer', None)
            cfg_api_.enabled = cfg.get('enabled', True)

    def add_eme_routes(self, file, integration, check_files=False):
        assert integration is not None

        r = load_settings(file, delimiters=('=>', '->')).conf

        # list lambdas
        for api_name, api in r.items():

            _api_type = integration
            if _api_type == 'rest':
                raise Exception("HTTPv1 not supported")

            cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))

            # if not cfg_api_.enabled:
            #     continue

            print(f"Processing routes: {api_name}")
            for endpoint, integ_opts in api.items():
                if endpoint.startswith('#'):
                    # ignore comments
                    continue

                method, route = endpoint.split(' ')

                endpoint_integ = self._get_integ(api_name, integ_opts, check_files, route, method)

                # add Api Gateway integration
                cfg_api_.routes.setdefault(route, TomcruRouteDescriptor(endpoint_integ.route, endpoint_integ.group, api_name))
                cfg_api_.routes[route].add_endpoint(endpoint_integ)

    def parser(self, p):
        return self.subparsers[p]

    def add_layer(self, layer_name, files=None, packages=None, folder=None, single_file=False, in_house=True):
        self.cfg.layers.append((layer_name, files, packages, folder, single_file, in_house))

    def _get_integ(self, api_name, integ_opts, check_files: bool, route, method) -> TomcruEndpointDescriptor:
        """

        :param integ_opts:
        :param check_files:
        :param route:
        :param method:
        :return:
        """
        if isinstance(integ_opts, str):
            integ_opts = [integ_opts]

        params = self._parse_linear_params(integ_opts)
        apicfg = self.cfg.apis[api_name]

        #integ_type, integ_id = integ_opts[0].split(':')
        # auth = self._get_param(integ_opts, 'auth', apicfg.default_authorizer)
        # if not auth: auth = None
        auth = params.get('auth', apicfg.default_authorizer)

        if 'lambda' in params:
            group, lamb_name = params['lambda'].split('/')
            layers = params.get('layers', apicfg.default_layers)
            role = params.get('role', apicfg.default_role)

            # post parse layers
            if isinstance(layers, str):
                layers = layers.split("|")
            if len(layers) > 0 and layers[0] == '': layers = layers.pop(0)

            # override

            if check_files:
                # check if files exist
                if not os.path.exists(f'{self.cfg.app_path}/lambdas/{group}/{lamb_name}'):
                    print("ERR: Lambda folder", group, lamb_name, 'does not exist!')
                    #continue
                    return None

            # Lambda integration
            integ = TomcruLambdaIntegrationDescription(group, route, method, lamb_name, layers, role, auth)
        elif 'swagger' in params:
            integ = TomcruSwaggerIntegration('swagger', route, method, auth, params['swagger'])
        else:
            print(params)
            raise Exception(f"Integration not recognized!")

        return integ

    def _get_auth_integ(self, auth_id, integ_opt) -> TomcruApiAuthorizerDescriptor:
        if not integ_opt:
            return None
        params = self._parse_linear_params(integ_opt)

        if 'lambda' in params:
            lambda_source, lambda_id = params['lambda'].split('/')

            return TomcruApiLambdaAuthorizerDescriptor(auth_id, lambda_id, lambda_source)
        elif 'oidc' in params:
            audience = params.get('audience')
            scopes = params.get('scopes')

            return TomcruApiOIDCAuthorizerDescriptor(auth_id, params['oidc'], audience, scopes)
        else:
            pass
        raise NotImplementedError("auth")

    def _parse_linear_params(self, line: list):
        if isinstance(line, str):
            if ',' in line:
                line = line.split(',')
            else:
                line = [line]

        params = {}
        for lparam in line:
            param = lparam.split(':')[0]

            value = lparam.removeprefix(param+':')
            # array values:
            if '|' in value:
                value = value.split('|')
            params[param] = value
        return params

    # def _get_param(self, integ_opts, param, default_val) -> str:
    #     r = next(filter(lambda x: x.startswith(param+':'), integ_opts), "").removeprefix(param+':')
    #
    #     if not r:
    #         # see if api config contains
    #         r = default_val
    #
    #     return r

    def add_envvars(self, file_path, env, vendor):
        """
        Adds enviornment variables ini file defined for:
        - lambda

        :param file_path: ini filepath
        :param env: environment to configure envvars for
        :param vendor: cloud vendor (aws | azure | gpc)
        :return:
        """
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.cfg.app_path, 'cfg', vendor, env, 'envvars', file_path)

        if not os.path.exists(file_path):
            raise Exception(f"Define your envvars in the following directory structure: project/cfg/{vendor}/<env>/envvars/<filename>.ini")

        self.cfg.envs[env].update(
            dict(load_settings(file_path).conf)
        )
