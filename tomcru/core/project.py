import os

from eme.entities import load_settings

from ..cfgparsers.SwaggerCfgParser import SwaggerCfgParser
from ..cfgparsers.BaseCfgParser import BaseCfgParser
from .cfg.api import TomcruCfg
from .modloader import load_serv


class TomcruProject:

    def __init__(self, app_path):
        self.app_path = app_path
        self.pck_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.cfgparser = None
        self.cfgs = {}
        self.services = {}
        self.appbuilders = {}
        self.active_cfg = None
        self.env = None

        self.debug_builders = False

    @property
    def cfg(self) -> TomcruCfg:
        return self.cfgs[self.active_cfg]

    def __enter__(self) -> BaseCfgParser:
        return self.cfgparser

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cfgparser.cfg:
            self.cfgs[self.cfgparser.name] = self.cfgparser.cfg

            if self.active_cfg is None:
                # default active cfg
                self.active_cfg = self.cfgparser.name

    def project_builder(self, name):
        # default cfg parser
        self.cfgparser = BaseCfgParser(self, name)
        self.cfgparser.create_cfg(self.app_path, self.pck_path)

        self.cfgparser.add_parser("swagger", SwaggerCfgParser(self, name))


        return self

    def build_app(self, app_type, env,  **kwargs):
        app_type, app_implement = app_type.split(':')
        path = os.path.join(self.cfg.pck_path, 'appbuilders', app_type.lower())
        self.env = env

        app_builder_factory = load_serv(path, app_implement.lower())

        if not app_builder_factory:
            raise Exception(f"AppBuilder {app_type}:{app_implement} not found")
        app_builder = app_builder_factory.app_builder(self, env, **kwargs)

        if not hasattr(app_builder, 'build_app'):
            raise Exception(f'App {app_type} does not have build_app! Path: {path}:{app_implement}')
        return app_builder.build_app(env), app_builder.run_apps

    def serv(self, name):
        if name not in self.services:
            self.load_serv(name)

        return self.services.get(name)

    def load_serv(self, name, srv=None):
        n = name.split(':')
        vendor, aim, service = n
        if not aim: aim = ''
        if not vendor: vendor = 'general'

        if srv is None:
            search_path = os.path.join(self.cfg.pck_path, 'services', vendor, aim)
            srv = load_serv(search_path, service)

            if srv is None:
                raise Exception(f"Service {vendor}/{aim}:{service} not found! Search path: {search_path}")

        # guess interface type
        if hasattr(srv, 'create_builder'):
            builder_cfg = self.load_serv_cfg(name)
            obj = srv.create_builder(self, builder_cfg)

            # imp = builder_cfg.get('__stack__.implementation')
            # if imp:
            #     # also load implementation
            #     search_path = os.path.join(self.cfg.pck_path, 'services', vendor, aim, 'implementations', imp)
            #     imp = load_serv(search_path, service)
            #     obj.imp = imp.create_implementation(self, builder_cfg)
        else:
            obj = srv

        self.services[name] = obj

    def load_serv_cfg(self, name):
        n = name.split(':')
        vendor, aim, service = n
        if not aim: aim = ''
        if not vendor: vendor = 'general'

        builder_cfg_file = os.path.join(self.cfg.app_path, 'cfg', vendor, self.env, aim, service + '.ini')
        if not os.path.exists(builder_cfg_file):
            # try loading cfg without env
            builder_cfg_file = os.path.join(self.cfg.app_path, 'cfg', vendor, aim, service + '.ini')

        if self.debug_builders:
            print(name, '->', builder_cfg_file)

        builder_cfg = load_settings(builder_cfg_file)
        builder_cfg.conf['__fileloc__'] = os.path.dirname(builder_cfg_file)

        return builder_cfg
