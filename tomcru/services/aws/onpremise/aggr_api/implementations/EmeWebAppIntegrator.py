import os

from flask import request

from tomcru import TomcruProject, TomcruEndpointDescriptor
from eme.entities import load_handlers

from .apps.EmeWebApi import EmeWebApi
from ..controllers.HomeController import HomeController


class EmeWebAppIntegrator:
    def __init__(self, project: TomcruProject, apigw_cfg):
        self.p = project
        self.cfg = project.cfg
        self.apigw_cfg = apigw_cfg

        self.app = None

    def create_app(self, api_name, apiopts):
        self.app = EmeWebApi(self.cfg.apis[api_name], apiopts)

        return self.app

    def load_eme_handlers(self, _controllers):
        # add api index controller
        webcfg = {"__index__": "Home:get_index"}
        _controllers['Home'] = HomeController(self.app)

        # @TODO: @later: add swagger pages? generate them or what?
        self.app.load_controllers(_controllers, webcfg)

        # include custom controllers
        _app_path = os.path.join(self.cfg.app_path, 'controllers')
        if os.path.exists(_app_path):
            self.app.load_controllers(load_handlers(self.app, 'Controller', path=_app_path), webcfg)

    def add_method(self, endpoint: TomcruEndpointDescriptor):
        """
        Adds method to EME/Flask app
        :param app: eme app (flask app)
        :param endpoint: endpoint url to hook to
        """
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
        aws_url_rule = str(request.url_rule).replace('<', '{').replace('>', '}')

        route = api.routes[aws_url_rule]
        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        return endpoint


create_implementation = EmeWebAppIntegrator
