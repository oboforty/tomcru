

class TomcruEndpointDescriptor:
    def __init__(self, group, route, method):
        """

        :param group:
        :param route:
        :param method:
        """
        self.route: str = route
        self.method: str = method
        self.group = group

        # self.integration: TomcruEndpointIntegration
        # self.lamb: str = lamb
        # self.layers = set(layers)
        # self.role: str = role

    def __repr__(self):
        return f'{self.method.upper()} {self.route} => {self.integ_id}'

    def __hash__(self):
        return self.endpoint_id

    @property
    def endpoint_id(self):
        # eme-like endpoint id (group & method name from lambda)
        return f'{self.group}:{self.method.lower()}_{self.integ_id}'

    @property
    def is_http(self):
        return not self.method or self.method == 'ws'

    @property
    def endpoint(self):
        return self.route


class TomcruLambdaIntegrationDescription(TomcruEndpointDescriptor):
    def __init__(self, group, route, method, lamb_name, layers, role, auth):
        """

        :param group:
        :param route:
        :param method:
        :param lamb_name:
        :param layers:
        :param role:
        :param auth:
        """
        super().__init__(group, route, method)

        self.lamb = lamb_name
        self.layers = layers
        self.role = role
        self.auth = auth

    @property
    def integ_id(self):
        return self.lamb

    @property
    def method_name(self):
        return f'{self.method.lower()}_{self.integ_id}'

    @property
    def lambda_id(self):
        return f'{self.group.lower()}/{self.lamb}'

    def __iter__(self):
        yield self.lamb
        yield self.layers
        yield self.role

