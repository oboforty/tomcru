from tomcru import TomcruProject


class SamAppBuilder:
    def __init__(self, project: TomcruProject, env, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.env = env
        self.apis = []
        #self.opts =

    def build_app(self, env):
        self.env = env

        for api_name, api in self.cfg.apis.items():
            api.api_name = api_name
            app = self.p.serv('aws:onpremise:aggr_api').build_api(api_name, api)

            self.apis.append(app)

        return self.apis

    def deploy_app(self, tpl_name='template.yaml'):
        raise NotImplementedError()
