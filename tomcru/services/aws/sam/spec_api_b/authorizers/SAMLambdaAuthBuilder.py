from tomcru import TomcruApiLambdaAuthorizerDescriptor
from core.utils.yaml_custom import Ref, Join


class SAMLambdaAuthBuilder:
    def __init__(self, param_builder, lambda_builder, external_authorizers):
        self.param_builder = param_builder
        self.lambda_builder = lambda_builder
        self.external_authorizers = external_authorizers

    def build(self, auth_id, auth: TomcruApiLambdaAuthorizerDescriptor, apiopts):
        role_id = self.param_builder.store('LambdaAccessRole', apiopts['access_role'])

        auth_integ = {
            'type': 'request',
            'identitySource': f"$request.{auth.src_in}.{auth.src_name}",
            'authorizerResultTtlInSeconds': 3600,
            'authorizerPayloadFormatVersion': 2.0,
            'enableSimpleResponses': True,
            'authorizerCredentials': Ref(role_id),
        }

        if 'external' == auth.lambda_source:
            arn = self.external_authorizers[auth.auth_id]
            auth_arn_param_id = self.param_builder.store(auth.auth_id + 'Arn', arn)

            # auth_integ['authorizerCredentials'] = Join(f'["", ["arn:aws:apigateway:", Ref: "AWS::Region",":lambda:path/2015-03-31/functions/", Ref: "{auth_arn_param_id}", "/invocations"]]')
            # auth_integ['authorizerCredentials'] = Join("tess")

            auth_integ['authorizerCredentials'] = Join(["", [
                "arn:aws:apigateway:",
                Ref("AWS::Region"),
                ":lambda:path/2015-03-31/functions/",
                Ref(auth_arn_param_id),
                "/invocations"
            ]])
        else:
            self.lambda_builder.add_lambda(auth.lambda_id)

            auth_integ['authorizerCredentials'] = auth.lambda_id.replace('/', '_') + '.Arn'

        return auth_integ
