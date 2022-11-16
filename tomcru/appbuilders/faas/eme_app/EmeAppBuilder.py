from tomcru import TomcruProject


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

    def get_object(self, srv, name=None):
        if name is None:
            srv, name = srv.split(':')
        objs = self.p.serv('aws:onpremise:obj_store')
        return objs.get(srv, name)

    def build_services(self):
        for srv, kwargs in self.cfg.extra_srv:
            self.p.serv(self.api2builder[srv]).init(**kwargs)

    def inject_dependencies(self):
        for srv, kwargs in self.cfg.extra_srv:
            self.p.serv(self.api2builder[srv]).inject_dependencies(**kwargs)

    def build_api(self, api_name, env):
        self.p.env = env

        api = self.cfg.apis[api_name]
        builder = self.p.serv(self.api2builder[api.api_type])

        return builder.build_api(api, env)

    def build_all(self, env):
        self.build_services()
        self.inject_dependencies()

        apps = []

        for api_name, api in self.cfg.apis.items():
            apps.append(self.build_api(api_name, env=env))

        return apps
