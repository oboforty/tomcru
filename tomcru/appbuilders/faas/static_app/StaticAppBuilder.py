from tomcru import TomcruProject, utils


class StaticAppBuilder:
    def __init__(self, project: TomcruProject, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.apis = []

        self.api2builder = {
            's3app': 'aws:onpremise:s3_static',

            # todo: call and build CloudFront, CF distribution and S3 bucket configs onpremise
        }

    def get_object(self, srv, name=None):
        if name is None:
            srv, name = srv.split(':')
        objs = self.p.serv('aws:onpremise:obj_store')
        return objs.get(srv, name)

    def build_app(self, env):
        self.p.env = env
        builder = self.p.serv(self.api2builder['s3app'])

        return builder.build_app(env)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
