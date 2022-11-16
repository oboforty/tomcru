


class TomcruApiAuthorizerDescriptor:
    def __init__(self, auth_id, auth_type, integ_id):
        """
        Describes authorizer for an API

        :param auth_type: lambda, lambda_external, iam, jwt
        :param integ_id: lambda name OR lambda ARN OR iam ARN OR jwt url
        """
        self.auth_id = auth_id
        self.auth_type = auth_type
        self.integ_id = integ_id


class TomcruApiLambdaAuthorizerDescriptor(TomcruApiAuthorizerDescriptor):
    def __init__(self, auth_id, lambda_id, lambda_source, src_in = None, src_name = None):
        """

        :param auth_type:
        :param lambda_id:
        """
        super().__init__(auth_id, 'lambda', lambda_id)
        self.lambda_source = lambda_source
        self.src_name = src_name
        self.src_in = src_in

    @property
    def lambda_id(self):
        return self.lambda_source+'/'+self.integ_id


class TomcruApiOIDCAuthorizerDescriptor(TomcruApiAuthorizerDescriptor):
    def __init__(self, auth_id, endpoint, audience, scopes):
        """

        :param auth_type:
        :param integ_id:
        """
        super().__init__(auth_id, 'oidc', endpoint)
        self.audience = audience
        self.scopes = scopes

    @property
    def endpoint_url(self):
        return self.integ_id
