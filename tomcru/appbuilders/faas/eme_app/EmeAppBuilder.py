from tomcru import TomcruProject

#from .flask_runner import start_flask_app


class EmeAppBuilder:
    def __init__(self, project: TomcruProject, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.apis = []
        #self.opts =

        # todo: add to configuration for sub-app types (ws/http/?)
        self.api2builder = {
            'http': 'aws:onpremise:aggr_api',
            'ws': 'aws:onpremise:aggr_ws',
            'mocked_api': 'aws:onpremise:mocked_api',
        }

    def build_api(self, api_name, env):
        self.p.env = env
        api = self.cfg.apis[api_name]

        return self.p.serv(self.api2builder[api.api_type]).build_api(api, env)

    # def build_app(self, env):
    #     self.env = env
    #
    #     for api_name, api in self.cfg.apis.items():
    #         if not api.enabled:
    #             continue
    #
    #         #api.api_name = api_name
    #         self.apis.append(app)
    #
    #     return self.apis
    #
    # def run_app(self, app, env, threaded=False):
    #     start_flask_app(app.api_name, app, env=env, threaded=threaded)
