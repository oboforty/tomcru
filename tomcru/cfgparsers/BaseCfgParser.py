import json
import os
from copy import deepcopy

from deepmerge import always_merger

from tomcru.core.utils.toml_custom import toml, load_settings, SettingWrapper
from tomcru.core.utils.yaml_custom import yaml

from ..core.utils.toml_custom import load_settings
from tomcru import TomcruSubProjectCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor, TomcruApiDescriptor, \
    TomcruApiLambdaAuthorizerDescriptor, TomcruLambdaIntegrationDescription, TomcruApiAuthorizerDescriptor, \
    TomcruSwaggerIntegrationDescription, TomcruApiOIDCAuthorizerDescriptor, TomcruMockedIntegrationDescription


class BaseCfgParser:
    def __init__(self, project, name):
        self.proj = project
        self.name = name
        self.cfg: TomcruSubProjectCfg | None = None

        self.subparsers = {}

    def __enter__(self) :
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cfg:
            #if self.active_cfg is None:
            # latest is active cfg

            # merge if needed
            merge = self.parser('merge')
            if merge:
                merge.do_merge()

    def create_cfg(self, path: str, pck_path):
        self.cfg = TomcruSubProjectCfg(path, pck_path)

    def add_parser(self, cfgpid, cfgp):
        if not cfgp.cfg:
            cfgp.cfg = self.cfg
        self.subparsers[cfgpid] = cfgp

    def parse_services(self):
        path = f'{self.cfg.app_path}/cfg'

        print(f"Tomcru: Parsing services in {self.cfg.app_path}")

        # merge toml files before parsing
        all_configs = {}
        swaggers = []

        # parse non-swagger config files
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)

                if file.endswith('.openapi.yaml') or file.endswith('.openapi.json') or file.endswith('.swagger.yaml') or file.endswith('.swagger.json'):
                    # handled by swagger cfg parser
                    swaggers.append(filepath)
                    continue
                elif file.endswith('.toml'):
                    cfg = toml.load(filepath)
                elif file.endswith('.yaml') or file.endswith('yml'):
                    cfg = yaml.load(filepath)
                    print(123123, '!!!! yaml file !!!', cfg)
                elif file.endswith('.json'):
                    with open(filepath) as fh:
                        cfg = json.load(fh)
                else:
                    raise NotImplementedError(filepath)

                if cfg:
                    always_merger.merge(all_configs, cfg)
                    del cfg

        # iterate config and break them up to services
        for serv, servcfg in all_configs.items():

            if serv == 'apigw':
                # eme/flask routes file - syntax is interpreted a bit differently
                settings = servcfg.pop('settings')
                default = servcfg.pop('default')

                apicfg = servcfg
                servcfg = settings

                if apicfg or default:
                   self.add_api_cfg(apicfg, default)

                if settings.get('parse_swagger', True):
                    for swagger_file in swaggers:
                        self.parser('swagger').add(swagger_file)

            self.add_service(serv, servcfg)

    def add_service(self, srv_id, cfg=None, **kwargs):
        if cfg is None:
            cfg = {}
        cfg = {**cfg, **kwargs}
        self.cfg.services[srv_id] = SettingWrapper(cfg)

    def add_api_cfg(self, apicfg: dict, cfg_all_: dict):

        # list lambdas and integrations
        for api_name, cfg in apicfg.items():
            _api_type = cfg.get('type', 'http')
            cfg = {**cfg_all_, **cfg}

            if _api_type == 'rest':
                raise NotImplementedError("HTTPv1 not supported")

            print(f"Processing api: {api_name}")

            #cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))
            cfg_api_ = self.cfg.apis[api_name] = TomcruApiDescriptor(api_name, _api_type)

            # map ini to tomcru descriptor
            cfg_api_.swagger_enabled = cfg.get('swagger_enabled', False)
            cfg_api_.swagger_ui = cfg.get('swagger_ui', False)
            cfg_api_.swagger_check_models = cfg.get('swagger_check_models', False)
            cfg_api_.default_authorizer = cfg.get('default_authorizer', None)
            cfg_api_.enabled = cfg.get('enabled', True)

            # list routes
            if 'routes' in cfg:
                self.add_eme_routes(api_name, cfg['routes'], check_files=True, subkey='')

            # add authorizers
            if 'authorizers' in cfg:
                # @TODO: put authorizers inside apis
                print("@TODO: authorizers inside apis")
                # authorizers = r.pop('authorizers', {})
                # # list authorizers
                # for auth_id, integ_opt in authorizers.items():
                #     auth_integ = self._get_auth_integ(auth_id, integ_opt)
                #
                #     self.cfg.authorizers[auth_id] = auth_integ

    def add_eme_routes(self, api_name: str, routes: dict, check_files=False, subkey=None):
        # assert integration is not None
        #
        # _api_type = integration
        #
        cfg_api_ = self.cfg.apis[api_name] #.setdefault(api_name, TomcruApiDescriptor(api_name, _api_type))

        if not cfg_api_.enabled:
            return

        print(f"Processing routes: {api_name}.{subkey}")
        for endpoint, integ_opts in routes.items():
            # if endpoint.startswith('#'):
            #     # ignore comments
            #     continue

            # todo: maybe we want integ options to be dict instead of a list?
            if isinstance(integ_opts, dict):
                # recursive parse
                self.add_eme_routes(api_name, integ_opts, check_files=check_files, subkey=endpoint)
            else:
                method, route = endpoint.split(' ')

                endpoint_integ = self._get_integ(api_name, integ_opts, check_files, route, method)

                # add Api Gateway integration
                if endpoint_integ:
                    cfg_api_.routes.setdefault(route, TomcruRouteDescriptor(endpoint_integ.route, endpoint_integ.group, api_name))
                    cfg_api_.routes[route].add_endpoint(endpoint_integ)

    def parser(self, p):
        return self.subparsers.get(p, None)

    def add_layer(self, layer_name, packages=None, /, folder=None, *, in_house=True):
        """
        Adds a python package as Lambda Layer for the project.

        :param layer_name: Layer's name as referenced within AWS and the Tomcru configuration. The zip file uploaded to Lambda also has this name
        :param packages: List of directories (python packages) to be added to the zip file.
        :param folder: Package path
        :param in_house: set true if the layer package is within the project (./layers/ directory)
        :return:
        """
        self.cfg.layers.append((layer_name, packages, folder, in_house))

    def _get_integ(self, api_name, integ_opts, check_files: bool, route, method) -> TomcruEndpointDescriptor | None:
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

            # TODO: ITT: fix parsing layers

            # post parse layers
            if isinstance(layers, str):
                layers = layers.split("|")
            if len(layers) > 0 and layers[0] == '': layers = layers.pop(0)

            # override

            if check_files:
                # check if files exist
                if not os.path.exists(f'{self.cfg.app_path}/lambdas/{group}/{lamb_name}'):
                    raise Exception(f"Lambda package {self.cfg.app_path}/lambdas/{group}/{lamb_name} doesn't exist")
                    return None

            # Lambda integration
            integ = TomcruLambdaIntegrationDescription(group, route, method, lamb_name, layers, role, auth, integ_opts)
        elif 'swagger' in params:
            integ = TomcruSwaggerIntegrationDescription('swagger', route, method, params['swagger'])
        elif 'mocked' in params:
            integ = TomcruMockedIntegrationDescription(params.get('group', 'Mocked'), route, method, params['mocked'])
        else:
            raise Exception(f"Integration not recognized!")

        return integ

    def _get_auth_integ(self, auth_id, integ_opt) -> TomcruApiAuthorizerDescriptor | None:
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
