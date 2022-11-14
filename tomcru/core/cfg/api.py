from collections import defaultdict
from typing import List, Dict, Set
from .authorizers import TomcruApiAuthorizerDescriptor
from .integrations import TomcruEndpointDescriptor


class TomcruCfg:
    def __init__(self, path: str, pck_path: str):
        """

        :param path:
        :param pck_path:
        """
        self.app_path = path + '/'
        self.pck_path = pck_path + '/'

        self.envs: Dict[str, Dict[str, dict]] = defaultdict(dict)

        self.apis: Dict[str, TomcruApiDescriptor] = {}
        self.authorizers: Dict[str, TomcruApiAuthorizerDescriptor] = {}

        self.layers = []
        self.extra_srv = []


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

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.route} ({self.group})>'
