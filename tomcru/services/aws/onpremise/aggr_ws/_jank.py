
import os


from tomcru import TomcruProject, TomcruEndpointDescriptor
from eme.entities import load_handlers

from .apps.EmeWsApp import EmeWsApp
from ..integration.LambdaWebsocketIntegration import LambdaWebsocketIntegration


class EmeWsAppIntegrator:
    WS_METHOD_PARAMS = ['route', 'msid', 'user', 'data', 'client', 'token']

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.p = project
        self.cfg = project.cfg
        self.apigw_cfg = apigw_cfg

        self.app = None

    def create_app(self, api_name, apiopts):
        self.app = EmeWsApp(self.cfg.apis[api_name], apiopts)

        return self.app

    def add_method(self, endpoint: TomcruEndpointDescriptor):
        """
        Adds method to EME/Flask app
        :param endpoint: endpoint url to hook to
        """

        self.app._endpoints_to_methods[endpoint.endpoint] = endpoint.endpoint_id
        # #self.app._methods[endpoint.endpoint_id] = (fn_to_call, self.WS_METHOD_PARAMS)
        #
        # # replace AWS APIGW route scheme to flask routing schema
        # _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        # self.app._custom_routes[endpoint.endpoint_id].add(_api_route)
        print(1)

    def load_eme_handlers(self, groups):
        webcfg = {}

        # groups are already added, no need to call load_groups
        # add generated controllers
        self.app.load_groups(groups, webcfg)
        self.app.debug_groups(webcfg)

        # replace autogenerated signature with <everything>
        for k, (fn, sig) in list(self.app._methods.items()):
            self.app._methods[k] = (fn, self.WS_METHOD_PARAMS)

        # include custom controllers
        _app_path = os.path.join(self.cfg.app_path, 'groups')
        if os.path.exists(_app_path):
            self.app.load_groups(load_handlers(self.app, 'Group', path=_app_path), webcfg)

    def post_to_conn(self, **kwargs):
        raise NotImplementedError()

    def get_called_endpoint(self, msid, user, client, token, data, route, **kwargs) -> TomcruEndpointDescriptor:

        return route

    def LambdaIntegration(self, *args, **kwargs):
        return LambdaWebsocketIntegration(self.app, *args, **kwargs)


create_implementation = EmeWsAppIntegrator
