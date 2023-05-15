import os

#from apispec import APISpec
from prance import ResolvingParser, BaseParser, ValidationError

from tomcru import TomcruSubProjectCfg, TomcruRouteEP, TomcruEndpoint, TomcruApiEP, \
    TomcruApiLambdaAuthorizerEP, TomcruLambdaIntegrationEP, TomcruMockedIntegrationEP, TomcruApiOIDCAuthorizerEP


class SwaggerCfgParser:
    def __init__(self, cfgparser, name):
        self.name = name
        self.cfg: TomcruSubProjectCfg | None = None

    def add_cfg(self, cfg):
        self.cfg = cfg

    def add(self, file, check_files=False):
        if not os.path.exists(file): raise Exception("File doesnt exist: " + file)

        try:
            f_resolved = ResolvingParser(file)
        except ValidationError as e:
            print("prance.ValidationError:")
            #errors = e.args[4]
            raise e
            exit()

        f = BaseParser(file)
        # spec = APISpec(
        #     title=f.specification['info']['title'],
        #     version=f.specification['info']['version'],
        #     openapi_version=f.semver,
        #     info=dict(f.specification['info']),
        # )
        api_name = f.specification['info']['title']

        # specification = yaml_utils.load_yaml_from_docstring(content)
        # #specification = yaml_utils.load_operations_from_docstring()
        cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiEP(api_name, 'http'))
        # cfg_api_.spec = {k: f.specification[k] for k in sorted(f.specification)} # add dict in key order
        # cfg_api_.spec_resolved_schemas = {k: f_resolved.specification[k] for k in sorted(f_resolved.specification)}
        cfg_api_.spec = dict(f.specification) # add dict in key order
        cfg_api_.spec_resolved_schemas = dict(f_resolved.specification)
        cfg_api_.swagger_file = file

        # if not cfg_api_.enabled:
        #     return
        components = f_resolved.specification.get('components', {})

        # parse authorizers
        if 'securitySchemes' in components:
            for auth_id, auth_spec in components['securitySchemes'].items():
                auth = self._get_authorizer(auth_id, auth_spec)
                self.cfg.authorizers[auth_id] = auth

        default_auth = self.cfg.authorizers.get(cfg_api_.default_authorizer)

        # integ opts refs
        # _integ_opts_ref = f.specification['components'].pop('x-integ-opts')

        # parse endpoints
        for route, path in f_resolved.specification['paths'].items():
            default_group = route.replace('/', '_').strip('_')

            for method, operation in path.items():
                method = method.upper()
                integ: TomcruEndpoint
                integ_opts = operation.pop('x-integ', {})

                if not integ_opts:
                    continue
                # if '$ref' in integ_opts:
                #     print("!!!!!!!!!!!", method, integ_opts)
                #     continue

                # parse lambda integration
                auth = integ_opts.pop('auth', default_auth)
                role = integ_opts.pop('role', None)

                # todo: support more integration types
                if integ_opts['type'] == 'lambda':
                    layers = integ_opts.pop('layers', [])
                    group, lamb = integ_opts.pop('lambda-id').split('/')

                    integ = TomcruLambdaIntegrationEP(route, method, group, lamb, layers, role, auth, integ_opts)
                elif integ_opts['type'] == 'mocked':
                    example = None

                    integ = TomcruMockedIntegrationEP(route, method, operation['operationId'], integ_opts.get('file'), example)
                else:
                    raise NotImplementedError(integ_opts.get('type'))

                # subset of the swagger is referenced from the tomcru cfg so that it can be modified for SAM building
                integ.spec_ref = operation

                cfg_api_.routes.setdefault(route, TomcruRouteEP(route, api_name))
                cfg_api_.routes[route].add_endpoint(integ)

    def _get_authorizer(self, auth_id, spec: dict):

        if spec['type'] == 'apiKey':
            # todo: is it possible to define non-lambda for this auth type?
            group, lambda_id, role, layers = self._get_lambda(spec.pop('x-lambda'))
            _in = spec.get('in', 'header')
            _name = spec.get('name', 'Authorization')

            return TomcruApiLambdaAuthorizerEP(auth_id, lambda_id, group, _in, _name)
        elif spec['type'] == 'openIdConnect':
            # openapi3 doesn't allow in/name for openIdConnect, so authorization header is set static

            # oidc endpoint is going to be redundant because SAM also requires it
            endpoint = spec['openIdConnectUrl']
            # oidc_cfg = spec.pop('x-oidc')

            return TomcruApiOIDCAuthorizerEP(auth_id, endpoint)
        elif spec['type'] == 'oauth2':
            raise NotImplementedError("we don't know how to implement this LOL")
        else:
            raise NotImplementedError("")
