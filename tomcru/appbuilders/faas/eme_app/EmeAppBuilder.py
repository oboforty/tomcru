from tomcru import TomcruProject

from .flask_runner import start_flask_app


class EmeAppBuilder:
    def __init__(self, project: TomcruProject, env, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.env = env
        self.apis = []
        #self.opts =

    def build_app(self, env):
        self.env = env

        for api_name, api in self.cfg.apis.items():
            if api.api_type == 'mocked_api':
                # build mocked server
                _app_serv = self.p.serv('aws:onpremise:mocked_api')
            else:
                _app_serv = self.p.serv('aws:onpremise:aggr_api')

            api.api_name = api_name
            app = _app_serv.build_api(api_name, api, env)
            self.apis.append(app)

        return self.apis

    def run_apps(self, apps, env):
        apps.sort(key=lambda x: x.is_main_thread)

        for app in apps:
            start_flask_app(app.api_name, app, env=env, threaded=not app.is_main_thread)
