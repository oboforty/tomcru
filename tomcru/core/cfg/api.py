from collections import defaultdict
from typing import List, Dict, Set

from .authorizers import TomcruApiAuthorizerDescriptor
from .integrations import TomcruEndpointDescriptor



class TomcruApiDescriptor:
    def __init__(self, api_name, api_type):
        """

        :param api_name:
        :param api_type:
        """
        self.api_name = api_name
        self.api_type = api_type # http | ws | rest

        # Api configuration:
        self.enabled = True
        self.routes: Dict[str, TomcruRouteDescriptor] = {}
        #self.authorizers: Set[str] = set()

        # OpenApi spec dict
        self.spec: dict | None = None
        self.spec_resolved_schemas: dict | None = None
        self.swagger_enabled = False
        self.swagger_ui = False
        self.swagger_file: str | None = None
        self.swagger_check_models = None

        # default integration values
        self.default_authorizer = None
        self.default_role = None
        self.default_layers = []

    def update(self, api: 'TomcruApiDescriptor'):
        if api.enabled is not None:
            self.enabled = api.enabled

        if self.api_name != api.api_name:
            raise f"Api name mismatch in update(): {self.api_name} != {api.api_name}"
        if self.api_type != api.api_type:
            raise f"Api name mismatch in update(): {self.api_type} != {api.api_type}"

        print('@TODO: merge self.spec = api.spec')
        print('@TODO: merge self.spec_resolved_schemas = api.spec_resolved_schemas')
        print('@TODO: merge self.swagger_enabled = api.swagger_enabled')
        print('@TODO: merge self.swagger_ui = api.swagger_ui')
        print('@TODO: merge self.swagger_file = api.swagger_file')
        print('@TODO: merge self.swagger_check_models = api.swagger_check_models')
        print('@TODO: merge self.default_authorizer = api.default_authorizer')
        print('@TODO: merge self.default_role = api.default_role')
        print('@TODO: merge self.default_layers = api.default_layers')

        # additive merge, not override
        route: TomcruRouteDescriptor
        for route_uri, route in api.routes.items():
            if route_uri in self.routes:
                self.routes[route_uri].update(route)
            else:
                self.routes[route_uri] = route

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.api_type.upper()} - {self.api_name}>'


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

    def update(self, route: 'TomcruRouteDescriptor'):
        if self.api_name != route.api_name:
            raise f"Route api name mismatch in update(): {self.api_name} != {route.api_name}"
        if self.group != route.group:
            raise f"Route group mismatch in update(): {self.group} != {route.group}"
        if self.route != route.route:
            raise f"Route route mismatch in update(): {self.route} != {route.route}"

        # additive merge, not override, but drop redundancies
        s = set()
        s.update(route.endpoints)
        s.update(self.endpoints)
        self.endpoints = list(s)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.route} ({self.group})>'
