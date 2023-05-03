import os


class TomcruEndpoint:

    def __init__(self, route, method, auth=None, opts=None):
        """

        :param group:
        :param route:
        :param method:
        """
        self.route: str = route
        self.method: str = method
        self.auth = auth
        self.integ_opts = opts if opts is not None else {}

        self.spec_ref: dict | None = None

        # self.integration: TomcruEndpointIntegration
        # self.lamb: str = lamb
        # self.layers = set(layers)
        # self.role: str = role

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.method.upper()} {self.route} => {self.integ_id}>'

    def __hash__(self):
        # @TODO: append with api name
        return hash(self.endpoint_id)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @property
    def endpoint_id(self):
        # eme-like endpoint id (group & method name from lambda)
        return f'{self.route}:{self.method.lower()}_{self.integ_id}'

    @staticmethod
    def get_endpoint_id(route, method, integ_id):
        # eme-like endpoint id (route & method name from lambda)
        return f'{route}:{method.lower()}_{integ_id}'

    @property
    def is_http(self):
        return not self.method or self.method == 'ws'

    @property
    def endpoint(self):
        return self.route

    @property
    def _tomcru_json_serializer(self):
        return self.endpoint_id


class TomcruLambdaIntegrationEP(TomcruEndpoint):

    def __init__(self, route, method, group, lamb_name, layers, role, auth, opts):
        """

        :param route:
        :param method:
        :param group: lambda group (parent directory)
        :param lamb_name: lambda name (lambda's directory name)
        :param layers: lambda layers attached
        :param role: execution role
        :param auth: authorizer attached
        """
        super().__init__(route, method, auth, opts)

        self.group = group
        self.lamb = lamb_name
        self.layers = layers
        self.role = role

    @property
    def integ_id(self):
        return self.lambda_id

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


class TomcruSwaggerIntegrationEP(TomcruEndpoint):
    def __init__(self, route, method, type):
        """

        :param route:
        :param method:
        :param type:
        """
        super().__init__(route, method, None)

        self.type = type
        if self.type == 'spec':
            _, req_content = os.path.splitext(self.route)
            self.req_content = req_content.lstrip('.')
        elif self.type == 'ui':
            self.req_content = 'html'
        else:
            raise Exception(type)

    @property
    def integ_id(self):
        return self.type + '_' + self.req_content

    @property
    def method_name(self):
        return f'{self.method.lower()}_{self.integ_id}'


class TomcruMockedIntegrationEP(TomcruEndpoint):
    def __init__(self, route, method, operationId, file, example):
        """

        :param route:
        :param method:
        :param resp:
        """
        super().__init__(route, method, None)

        self.file = file
        self.exmple = example
        self.source = 'file' if file else 'example'
        self.operationId = operationId

    @property
    def integ_id(self):
        return os.path.basename(self.operationId)

    @property
    def method_name(self):
        return f'{self.method.lower()}_{self.integ_id}'
