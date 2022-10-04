import yaml

from tomcru import TomcruProject, TomcruApiDescriptor, TomcruEndpointDescriptor, TomcruLambdaIntegrationDescription, TomcruApiLambdaAuthorizerDescriptor
from tomcru.utils import Ref, GetAtt, Join


class SwaggerApiTemplater:

    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.lambda_builder = project.serv('aws:sam:lambda_b')
        self.param_builder = project.serv('aws:sam:params_b')

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

        if 'securitySchemes' in spec.get('components', {}):

            for auth_id, auth_spec in spec['components']['securitySchemes'].items():
                auth = self.cfg.authorizers[auth_id]

                apiopts = self.opts.get('__default__', {})
                apiopts.update(self.opts.get(api.api_name, {}))

                role_id = self.param_builder.store('LambdaAccessRole', apiopts['access_role'])

                if isinstance(auth, TomcruApiLambdaAuthorizerDescriptor):
                    auth_integ = {
                        'type': 'request',
                        'identitySource': "$request.header.Authorization",
                        'authorizerResultTtlInSeconds': 3600,
                        'authorizerPayloadFormatVersion': 2.0,
                        'enableSimpleResponses': True,
                        'authorizerCredentials': Ref(role_id),
                    }

                    # if 'external' == auth.lambda_source:
                    #     authArnParamId = auth.auth_id+'Arn'
                    #     auth_integ['authorizerUri'] = Join(f'["", ["arn:aws:apigateway:", Ref: "AWS::Region",":lambda:path/2015-03-31/functions/", Ref: "{authArnParamId}", "/invocations"]'),
                else:
                    raise NotImplementedError(str(type(auth)))

                auth_spec['x-amazon-apigateway-authorizer'] = auth_integ

    def _build_endpoints(self, spec, api: TomcruApiDescriptor):
        for route, ops in spec['paths'].items():

            for method, op in ops.items():
                integ = None

                if 'x-lambda' in op:
                    lambda_id, integ = self._integrate_lambda(op.pop('x-lambda'), api, route, method)

                    self.lambda_builder.add_lambda(lambda_id)
                else:
                    print('???', op)

                    # todo: aws-mock integration if nothing is here?

                if integ:
                    op['x-amazon-apigateway-integration'] = integ
                else:
                    raise Exception(f"No integration found for {method} {route}")

    def _integrate_lambda(self, lambda_id, api, route, method):
        if not isinstance(lambda_id, str):
            lambda_id = lambda_id['lambda-id']

        group, lamb = lambda_id.split('/')
        ep_id = TomcruEndpointDescriptor.get_endpoint_id(group, method, lamb)

        route_cfg = api.routes[route]
        integ_cfg: TomcruLambdaIntegrationDescription = next(filter(lambda x: x.endpoint_id == ep_id, route_cfg.endpoints))

        integ = {
            'type': "aws_proxy",
            'httpMethod': "POST",
            'uri': GetAtt(f"{group}_{lamb}.Arn"),
            # todo: configure timeout?
            'timeoutInMillis': 3000,
            'payloadFormatVersion': "2.0"
        }

        if integ_cfg.role:
            role_id = self.param_builder.store('LambdaAccessRole', integ_cfg.role)

            integ['credentials'] = Ref(role_id)

        # lambda integration
        return lambda_id, integ
