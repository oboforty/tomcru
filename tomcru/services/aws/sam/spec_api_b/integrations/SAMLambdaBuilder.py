from tomcru import TomcruRouteDescriptor, TomcruLambdaIntegrationDescription
from core.utils.yaml_custom import GetAtt, Ref


class SAMLambdaBuilder:
    def __init__(self, param_builder, lambda_builder):
        self.param_builder = param_builder
        self.lambda_builder = lambda_builder

    def build(self, integ_cfg: TomcruLambdaIntegrationDescription):
        integ = {
            'type': "aws_proxy",
            'httpMethod': "POST",
            'uri': GetAtt(f"{integ_cfg.group}_{integ_cfg.lambda_id}.Arn"),
            # todo: configure timeout?
            'timeoutInMillis': 3000,
            'payloadFormatVersion': "2.0"
        }

        if integ_cfg.role:
            role_id = self.param_builder.store('LambdaAccessRole', integ_cfg.role)

            integ['credentials'] = Ref(role_id)

        # lambda integration
        return integ
