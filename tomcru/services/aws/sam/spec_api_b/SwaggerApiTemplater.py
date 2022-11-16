from tomcru import TomcruProject, TomcruApiDescriptor, TomcruEndpointDescriptor, TomcruLambdaIntegrationDescription, TomcruApiLambdaAuthorizerDescriptor, TomcruApiOIDCAuthorizerDescriptor, TomcruRouteDescriptor

from .integrations.SAMLambdaBuilder import SAMLambdaBuilder
from .authorizers.SAMLambdaAuthBuilder import SAMLambdaAuthBuilder
from .authorizers.SAMOIDCAuthBuilder import SAMOIDCAuthBuilder


class SwaggerApiTemplater:

    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.lambda_builder = project.serv('aws:sam:lambda_b')
        self.param_builder = project.serv('aws:sam:params_b')

        self.integrations_b: dict[type, object] = {
            TomcruLambdaIntegrationDescription: SAMLambdaBuilder(self.param_builder, self.lambda_builder)
        }

        self.authorizers_b: dict[type, object] = {
            TomcruApiLambdaAuthorizerDescriptor: SAMLambdaAuthBuilder(self.param_builder, self.lambda_builder, self.opts['external_authorizers']),
            TomcruApiOIDCAuthorizerDescriptor: SAMOIDCAuthBuilder(self.param_builder)
        }

    def build_api(self, api: TomcruApiDescriptor, env: str):
        # todo: stage var
        # todo: env var?

        # hat tesomsz mit kell ezt csurni-csavarni
        spec = dict(api.spec)

        self._build_authorizers(spec, api)

        self._build_endpoints(spec, api)

        return {
            'Type': 'AWS::Serverless::HttpApi',
            'Properties': {
                'StageName': 'v1',
                'DefinitionBody': spec
            }
        }

    def _build_authorizers(self, spec, api: TomcruApiDescriptor):
        components = spec.get('components', {})

        if 'securitySchemes' in components:
            for auth_id, auth_spec in components['securitySchemes'].items():
                auth = self.cfg.authorizers[auth_id]

                apiopts = self.opts.get('__default__', {})
                apiopts.update(self.opts.get(api.api_name, {}))

                auth_builder = self.authorizers_b[type(auth)]
                auth_spec['x-amazon-apigateway-authorizer'] = auth_builder.build(auth_id, auth, apiopts)

    def _build_endpoints(self, spec, api: TomcruApiDescriptor):

        ro: TomcruRouteDescriptor
        for route, ro in api.routes.items():

            endpoint: TomcruEndpointDescriptor
            for endpoint in ro.endpoints:
                op = endpoint.spec_ref

                if not op:
                    print("        MISSING SWAGGER REF for", endpoint)
                    continue

                integ_builder = self.integrations_b[type(endpoint)]
                op['x-amazon-apigateway-integration'] = integ_builder.build(endpoint)

                if endpoint.auth:
                    op['security'] = [{endpoint.auth: []}]
