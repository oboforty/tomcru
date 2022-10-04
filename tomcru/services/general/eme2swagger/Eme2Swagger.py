from collections import defaultdict

from tomcru import TomcruProject, TomcruApiDescriptor, TomcruLambdaIntegrationDescription, TomcruApiLambdaAuthorizerDescriptor


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

            if isinstance(auth, TomcruApiLambdaAuthorizerDescriptor):
                auth_integ = {
                    'type': 'apiKey',
                    'name': auth.auth_id,
                    'in': "header"
                }

                # no need to define it further than this at this level
                # if 'external' == auth.lambda_source:
                # else:
            else:
                # todo: support more authorizers
                raise NotImplementedError()

            authorizers[auth.auth_id] = auth_integ

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
                    'layers': endpoint.layers
                }
            }
        else:
            raise NotImplementedError(str(endpoint))
