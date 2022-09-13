from tomcru import TomCruProject


class EmeAppBuilder:
    def __init__(self, project: TomCruProject, **kwargs):
        self.p = project
        self.cfg = project.cfg
        #self.opts =

    def build_app(self):
        self.app = None # todo:eme app

        self.p.serv('aws:local_mock:boto3').inject_boto()

        for api_name, api in self.cfg.apis.items():
            self.p.serv(f'aws:aggr_flak_eme:apigw_{api.api_type}').build_api(api_name, api, self.app)
