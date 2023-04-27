import os

#from apispec import APISpec
from prance import ResolvingParser, BaseParser

from tomcru import TomcruSubProjectCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor, TomcruApiDescriptor, \
    TomcruApiLambdaAuthorizerDescriptor, TomcruLambdaIntegrationDescription, TomcruApiAuthorizerDescriptor, TomcruApiOIDCAuthorizerDescriptor


class SwaggerCfgParser:
    def __init__(self, cfgparser, name):
        self.name = name
        self.cfg: TomcruSubProjectCfg | None = None

    def add_cfg(self, cfg):
        self.cfg = cfg

    def add(self, file, check_files=False):
        if not os.path.exists(file): raise Exception("File doesnt exist: " + file)

        f_resolved = ResolvingParser(file)

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
        cfg_api_ = self.cfg.apis.setdefault(api_name, TomcruApiDescriptor(api_name, 'http'))
        # cfg_api_.spec = {k: f.specification[k] for k in sorted(f.specification)} # add dict in key order
        # cfg_api_.spec_resolved_schemas = {k: f_resolved.specification[k] for k in sorted(f_resolved.specification)}
        cfg_api_.spec = dict(f.specification) # add dict in key order
        cfg_api_.spec_resolved_schemas = dict(f_resolved.specification)
        cfg_api_.swagger_file = file

        # if not cfg_api_.enabled:
        #     return
        components = f.specification.get('components', {})

        # parse authorizers
        if 'securitySchemes' in components:
            for auth_id, auth_spec in components['securitySchemes'].items():
                auth = self._get_authorizer(auth_id, auth_spec)
                self.cfg.authorizers[auth_id] = auth

        default_auth = next(iter(self.cfg.authorizers)) if len(self.cfg.authorizers)==1 else None

        # parse endpoints
        for route, path in f.specification['paths'].items():
            #group = route.replace('/', '_').strip('_')

            for method, operation in path.items():
                method = method.upper()
                auth = operation.pop('x-auth', default_auth)
                integ: TomcruEndpointDescriptor

                integ_opts = operation.pop('x-integ', {})
                if integ_opts:
                    if integ_opts['type'] != 'lambda':
                        raise NotImplementedError("")

                    # parse lambda integration
                    group, lamb, role, layers = self._get_lambda(integ_opts)

                    integ = TomcruLambdaIntegrationDescription(group, route, method, lamb, layers, role, auth, integ_opts)

                # subset of the swagger is referenced from the tomcru cfg so that it can be modified for SAM building
                integ.spec_ref = operation

                cfg_api_.routes.setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                cfg_api_.routes[route].add_endpoint(integ)

    def _get_authorizer(self, auth_id, spec: dict):

        if spec['type'] == 'apiKey':
            # todo: is it possible to define non-lambda for this auth type?
            group, lambda_id, role, layers = self._get_lambda(spec.pop('x-lambda'))
            _in = spec.get('in', 'header')
            _name = spec.get('name', 'Authorization')

            return TomcruApiLambdaAuthorizerDescriptor(auth_id, lambda_id, group, _in, _name)
        elif spec['type'] == 'openIdConnect':
            # openapi3 doesn't allow in/name for openIdConnect, so authorization header is set static

            # oidc endpoint is going to be redundant because SAM also requires it
            endpoint = spec['openIdConnectUrl']
            oidc_cfg = spec.pop('x-oidc')

            return TomcruApiOIDCAuthorizerDescriptor(auth_id, endpoint, oidc_cfg.get('audience'), oidc_cfg.get('scopes'))
        elif spec['type'] == 'oauth2':
            raise NotImplementedError("we don't know how to implement this LOL")
        else:
            raise NotImplementedError("")

    def _get_lambda(self, lamb):
        role, layers = None, []

        if isinstance(lamb, dict):
            lamb, role, layers = lamb['lambda-id'], lamb.get('role'), lamb.get('layers')
        elif not isinstance(lamb, str):
            raise Exception("Lambda integration as array not supported")

        # fetch endpoint
        group, integ_id = lamb.split('/')
        return group, integ_id, role, layers
