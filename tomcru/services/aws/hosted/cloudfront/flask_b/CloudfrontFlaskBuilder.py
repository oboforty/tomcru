import os


from tomcru.core.cfg.api import TomcruApiEP
from tomcru.services.ServiceBase import ServiceBase
from tomcru.core import utils
from flask import Flask
from tomcru_jerry.static import StaticWebsite

__dir__ = os.path.dirname(os.path.realpath(__file__))


class CloudfrontFlaskBuilder(ServiceBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps: dict[str, Flask] = {}

    def get_app(self, api_name):
        if api_name not in self.apps:

            raise Exception(f"Api {api_name} not found! Available apis: {', '.join(self.apps.keys())}")
        return self.apps[api_name], self.opts.get(f'apis.{api_name}', {})

    def inject_dependencies(self):
        for app_name, app_cfg in self.cfg.get('static_apps').items():
            self._build_static_app(app_name, app_cfg)

    def init(self):
        pass

    def deject_dependencies(self):
        pass

    def _build_static_app(self, app_name, app_cfg):
        path = os.path.join(self.env.app_path, app_cfg.get('path', os.path.join('static', app_name)))
        index = app_cfg.get('index', 'index.html')
        static_files = app_cfg.get('static_files', ['img', 'css', 'js'])
        params = self.opts.get(f'static_apps.{app_name}.params')

        appbuilder = StaticWebsite(index, path, static_files)
        appbuilder.build(**params)

        self.apps[app_name] = appbuilder.app

    def create_app(self, api: TomcruApiEP, apiopts: dict):
        port = apiopts.get('port', 5000)

        api_id = f'{api.api_name}:{port}'
        app = Flask(api_id)

        # set custom attributes
        app.api_name = api_id
        app.api_type = 'http'
        app.is_main_thread = apiopts.get('main_api', False)

        return app
