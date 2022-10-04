import os

from apispec import APISpec
from prance import ResolvingParser, BaseParser


from tomcru import TomcruCfg, TomcruRouteDescriptor, TomcruEndpointDescriptor, TomcruApiDescriptor, \
    TomcruApiLambdaAuthorizerDescriptor, TomcruLambdaIntegrationDescription, TomcruApiAuthorizerDescriptor


class SwaggerCfgParser:
    def __init__(self, project, name):
        self.proj = project
        self.name = name
        self.cfg: TomcruCfg | None = None

    def add_cfg(self, cfg):
        self.cfg = cfg

    def add(self, api_name, check_files=False):
        file = os.path.join(self.cfg.app_path, 'cfg', 'apis', api_name+'.yaml')
        if not os.path.exists(file): file = file[:-4] + '.yml'
        if not os.path.exists(file): raise Exception("File doesnt exist: " + file)

        f_resolved = ResolvingParser(file)
        f = BaseParser(file)
        # spec = APISpec(
        #     title=f.specification['info']['title'],
        #     version=f.specification['info']['version'],
        #     openapi_version=f.semver,
        #     info=dict(f.specification['info']),
        # )

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

        for route, path in f.specification['paths'].items():
            #group = route.replace('/', '_').strip('_')

            for method, operation in path.items():
                method = method.upper()

                # parse lambda integration
                lamb, role, layers, auth = operation['x-lambda'], None, [], None
                if isinstance(lamb, dict):
                    lamb, role, layers, auth = lamb['lambda-id'], lamb.get('role'), lamb.get('layers'), lamb.get('auth')
                elif not isinstance(lamb, str):
                    raise Exception("Lambda integration as array not supported")

                group, lamb = lamb.split('/')

                integ = TomcruLambdaIntegrationDescription(group, route, method, lamb, layers, role, auth)

                cfg_api_.routes.setdefault(route, TomcruRouteDescriptor(route, group, api_name))
                cfg_api_.routes[route].add_endpoint(integ)
