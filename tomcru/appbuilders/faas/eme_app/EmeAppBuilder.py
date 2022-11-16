from tomcru import TomcruProject, utils


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

    def init_services(self):
        # ws and http eme builders register their app objects to a common obj_store item
        self.cfg.services.append(('http', {}))
        self.cfg.services.append(('ws', {}))
        self.cfg.services.append(('aws:onpremise:lambda_b', {}))
        self.cfg.services.append(('aws:onpremise:apigatewaymanagementapi', {}))

        for srv, kwargs in self.cfg.services:
            service = self.p.serv(self.api2builder.get(srv, srv))
            service.init(**kwargs)

    def inject_dependencies(self):
        for srv, _ in self.cfg.services:
            service = self.p.serv(self.api2builder.get(srv, srv))
            if hasattr(service, 'inject_dependencies'):
                service.inject_dependencies()

    def deject_dependencies(self):
        for srv, _ in self.cfg.services:
            service = self.p.serv(self.api2builder.get(srv, srv))

            if hasattr(service, 'deject_dependencies'):
                service.deject_dependencies()

        utils.cleanup_injects()

    def build_api(self, api_name, env):
        self.p.env = env

        api = self.cfg.apis[api_name]
        builder = self.p.serv(self.api2builder[api.api_type])

        return builder.build_api(api, env)

    def build_all(self, env):
        self.init_services()

        apps = []

        for api_name, api in self.cfg.apis.items():
            self.inject_dependencies()

            apps.append(self.build_api(api_name, env=env))

            self.deject_dependencies()

        return apps
