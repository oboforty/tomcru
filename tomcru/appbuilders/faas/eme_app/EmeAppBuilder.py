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

        self.p.serv('aws:local_mock:boto3_b').inject_boto()

        for api_name, api in self.cfg.apis.items():
            app = self.p.serv(f'aws:aggr_flask_eme:apigw_{api.api_type}').build_api(api_name, api)

            self.apis.append(app)

        return self.apis

    def run_apps(self, apps, env):

        for app in apps:
            start_flask_app(app)
