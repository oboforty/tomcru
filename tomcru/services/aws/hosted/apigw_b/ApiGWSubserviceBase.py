from abc import ABCMeta, abstractmethod
import logging
import os.path
from typing import Callable

from tomcru.services.ServiceBase import ServiceBase
from tomcru import TomcruApiEP, TomcruEndpoint
from .TomcruApiGWAuthorizerIntegration import TomcruApiGWAuthorizerIntegration

__dir__ = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('tomcru')


class ApiGWSubserviceBase(ServiceBase, metaclass=ABCMeta):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.integrations: dict[TomcruEndpoint, Callable] = {}
        self.authorizers: dict[str, TomcruApiGWAuthorizerIntegration] = self.p.cfg.authorizers
        self.parent = parent

    @abstractmethod
    def create_app(self, api: TomcruApiEP, apiopts: dict):
        pass

    @abstractmethod
    def build_api(self, api: TomcruApiEP, apiopts: dict):
        pass

    def get_called_endpoint(self, *, port, route_key, vendor_endpoint, **kwargs) -> tuple[TomcruEndpoint, TomcruApiEP] | tuple[None, None]:
        # find api name by port
        api_names = self.parent.port2apps[port]

        for api_name in api_names:
            api = self.p.cfg.apis[api_name]
            api_root = self.opts.get(f'apis.{api.api_name}.api_root')
            if api_root:
                route_key = route_key.removeprefix(api_root)

            route = api.routes.get(route_key)

            if not route:
                # continue searching for integration
                continue

            # search for endpoint in route
            endpoint = next(filter(lambda x: x.endpoint_id == vendor_endpoint, route.endpoints), None)
            return endpoint, api

        return None, None
