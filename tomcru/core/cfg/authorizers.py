


class TomcruApiAuthorizerDescriptor:
    def __init__(self, auth_type, integ_id):
        """
        Describes authorizer for an API

        :param auth_type: lambda, lambda_external, iam, jwt
        :param integ_id: lambda name OR lambda ARN OR iam ARN OR jwt url
        """
        self.auth_type = auth_type
        self.integ_id = integ_id


class TomcruApiLambdaAuthorizerDescriptor(TomcruApiAuthorizerDescriptor):
    def __init__(self, auth_id, integ_id, lambda_source):
        """

        :param auth_type:
        :param integ_id:
        """
        super().__init__('lambda', integ_id)

        self.auth_id = auth_id
        self.lambda_source = lambda_source

    @property
    def lambda_id(self):
        return self.lambda_source+'/'+self.integ_id
