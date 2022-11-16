from collections import defaultdict

from tomcru import TomcruProject, TomcruApiDescriptor, TomcruLambdaIntegrationDescription, TomcruApiLambdaAuthorizerDescriptor, TomcruSwaggerIntegrationDescription


class Eme2Swagger:

    def __init__(self, project: TomcruProject, opts: dict):
        self.p = project
        self.cfg = project.cfg
        self.opts = opts

    def convert_to_swagger(self, api: TomcruApiDescriptor):
        paths = defaultdict(dict)

        # define authorizers used by this api, based on the lambda integrations
        api_authorizers = set()

        for route, route_cfg in api.routes.items():
            for endpoint in route_cfg.endpoints:
                paths[route][endpoint.method] = {
                    #'summary': endpoint,
                    'operationId': endpoint.endpoint_id,
                    **self.get_integ(endpoint, api_authorizers),
                }

        authorizers = {}

        for authorizer_id in api_authorizers:
            auth = self.cfg.authorizers[authorizer_id]

            authorizers[auth.auth_id] = {
                'type': auth.auth_type,
                'name': auth.auth_id,
                'in': auth.src_in
            }

        return {
            'openapi': "3.0.0",
            'info': {
                # todo: include api version & description to cfg
                'version': '1.0.0',
                'title': api.api_name,
                'license': {
                    'name': "MIT"
                }
            },
            #'servers': [{'url': ''}]
            'paths': dict(paths),
            'components': {
                'securitySchemes': authorizers
            }
        }

    def get_integ(self, endpoint, authorizers_discovered: set):
        if endpoint.auth:
            authorizers_discovered.add(endpoint.auth)

        if isinstance(endpoint, TomcruLambdaIntegrationDescription):
            return {
                'x-lambda': {
                    'lambda-id': endpoint.lambda_id,
                    'role': endpoint.role,
                    'layers': endpoint.layers,
                    'auth': endpoint.auth
                }
            }
        elif isinstance(endpoint, TomcruSwaggerIntegrationDescription):
            return {}
        else:
            raise NotImplementedError(str(endpoint))
