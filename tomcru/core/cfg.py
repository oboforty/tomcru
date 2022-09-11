from collections import defaultdict
from typing import List, Dict
import os


class TomcruCfg:
    def __init__(self, path: str):
        #self.tpl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "samapp/tpl")
        self.app_path = path + '/'

        self.envs = {}

        self.apis: Dict[Dict[TomcruRouteDescriptor]] = defaultdict(dict)
        self.wss: Dict[Dict[TomcruRouteDescriptor]] = defaultdict(dict)
        self.tasks = {}

        self.lambdas = set()
        self.layers = []


class TomcruRouteDescriptor:

    def __init__(self, route, group, api_name):
        self.api_name = api_name
        self.group = group
        self.route = route
        self.endpoints: List[TomcruEndpointDescriptor] = []

    def add_endpoint(self, ep):
        self.endpoints.append(ep)

    def __repr__(self):
        return f'{self.route} ({self.group})'


class TomcruEndpointDescriptor:
    def __init__(self, group, route, method, lamb, role, layers):
        self.route: str = route
        self.method: str = method
        self.lamb: str = lamb
        self.layers = set(layers)
        self.role: str = role
        self.group = group

    def __repr__(self):
        return f'{self.method.upper()} {self.route} => {self.lamb}'

    @property
    def endpoint_id(self):
        # eme-like endpoint id (group & method name from lambda)
        return f'{self.group}:{self.method.lower()}_{self.lamb}'

    @property
    def is_http(self):
        return not self.method or self.method == 'ws'

    @property
    def endpoint(self):
        return self.route

    @property
    def method_name(self):
        return f'{self.method.lower()}_{self.lamb}'

    def __iter__(self):
        yield self.group
        yield self.lamb
        yield self.layers
