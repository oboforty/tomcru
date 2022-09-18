from collections import defaultdict
from typing import List, Dict, Set
import os


class TomcruCfg:
    def __init__(self, path: str, pck_path: str):
        """

        :param path:
        :param pck_path:
        """
        self.app_path = path + '/'
        self.pck_path = pck_path + '/'

        self.envs = {}

        self.tasks = {}
        self.apis: Dict[str, TomcruApiDescriptor] = {}
        self.lambdas = set()
        self.layers = []
        self.authorizers: Dict[str, TomcruApiAuthorizerDescriptor] = {}


class TomcruApiDescriptor:
    def __init__(self, api_name, api_type):
        """

        :param api_name:
        :param api_type:
        """
        self.api_name = api_name
        self.api_type = api_type # http | ws | rest
        self.routes: Dict[TomcruRouteDescriptor] = {}

        self.swagger_enabled = False
        self.swagger_ui = False
        self.default_authorizer = None
        self.authorizers: Set[str] = set()


class TomcruRouteDescriptor:

    def __init__(self, route, group, api_name):
        """

        :param route:
        :param group:
        :param api_name:
        """
        self.api_name = api_name
        self.group = group
        self.route = route
        self.endpoints: List[TomcruEndpointDescriptor] = []

    def add_endpoint(self, ep):
        self.endpoints.append(ep)

    def __repr__(self):
        return f'{self.route} ({self.group})'


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

    def __iter__(self):
        yield self.lamb
        yield self.layers
        yield self.role


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
    def __init__(self, auth_type, integ_id, lambda_source):
        """

        :param auth_type:
        :param integ_id:
        """
        super().__init__(auth_type, integ_id)

        self.lambda_source = lambda_source
