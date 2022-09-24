
import os


from tomcru import TomcruProject, TomcruEndpointDescriptor
from eme.entities import load_handlers

from .apps.EmeWsApp import EmeWsApp


class EmeWsAppIntegrator:
    WS_METHOD_PARAMS = ['route', 'msid', 'user', 'data', 'client', 'token']

    def __init__(self, project: TomcruProject, apigw_cfg):
        self.p = project
        self.cfg = project.cfg
        self.apigw_cfg = apigw_cfg

        self.app = None

    def create_app(self, apiopts):
        self.app = EmeWsApp(self.cfg, apiopts)

        return self.app

    def load_eme_handlers(self, groups):
        webcfg = {}

        # groups are already added, no need to call load_groups
        # add generated controllers
        #self.app.load_groups(groups, webcfg)
        self.app.debug_groups(webcfg)

        # include custom controllers
        _app_path = os.path.join(self.cfg.app_path, 'groups')
        if os.path.exists(_app_path):
            self.app.load_groups(load_handlers(self.app, 'Group', path=_app_path), webcfg)

    def add_method(self, endpoint: TomcruEndpointDescriptor, fn_to_call=None):
        """
        Adds method to EME/Flask app
        :param app: eme app (flask app)
        :param endpoint: endpoint url to hook to
        """
        assert fn_to_call is not None

        self.app._endpoints_to_methods[endpoint.endpoint] = endpoint.endpoint_id
        self.app._methods[endpoint.endpoint_id] = (fn_to_call, self.WS_METHOD_PARAMS)


        # replace AWS APIGW route scheme to flask routing schema
        _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        self.app._custom_routes[endpoint.endpoint_id].add(_api_route)

    def post_to_conn(self, **kwargs):
        raise NotImplementedError()

    def get_called_endpoint_id(self) -> str:
        """
        Gets abstract endpoint id from flask request
        :return:
        """
        ep = request.endpoint
        group, method_name = ep.split(':')
        method, integ_id = method_name.split("_")

        # todo: but isn't this the exact same as request.endpoint?
        return f'{group}:{method.lower()}_{integ_id}'

    def get_called_endpoint(self) -> TomcruEndpointDescriptor:
        # @TODO: how to fetch right api?
        api = next(iter(self.cfg.apis.values()))

        route = api.routes[str(request.url_rule)]
        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        return endpoint


create_implementation = EmeWsAppIntegrator
