from tomcru import TomcruProject

#from .flask_runner import start_flask_app


class EmeAppBuilder:
    def __init__(self, project: TomcruProject, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.apis = []

        # todo: add to configuration for sub-app types (ws/http/?)
        self.api2builder = {
            'http': 'aws:onpremise:aggr_api',
            'ws': 'aws:onpremise:aggr_ws',
            'mocked_api': 'aws:onpremise:mocked_api',

            'dynamodb': 'aws:onpremise:dynamodb_reldb',
            'boto3': 'aws:onpremise:boto3_b',
        }

    def build_api(self, api_name, env):
        self.p.env = env

        for srv, kwargs in self.cfg.extra_srv:
            self.p.serv(self.api2builder[srv]).init(**kwargs)

        api = self.cfg.apis[api_name]
        return self.p.serv(self.api2builder[api.api_type]).build_api(api, env)
