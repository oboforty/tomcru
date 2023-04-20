import os

from tomcru import TomcruProject
from core.utils.yaml_custom import yaml


class SamAppBuilder:

    def __init__(self, project: TomcruProject, **kwargs):
        self.p = project
        self.cfg = project.cfg
        self.apis = []
        #self.opts =

        self.param_builder = project.serv('aws:sam:params_b')

    def build_app(self, env):
        self.p.env = env
        lambda_builder = self.p.serv('aws:sam:lambda_b')

        sam_tpl: dict = self.build_app_stack(env)

        # buidl globals
        sam_tpl['Globals']['Function'] = lambda_builder.build_lambda_globals()

        # build apis
        for api_name, api in self.cfg.apis.items():
            if not api.enabled:
                continue

            if not api.spec:
                # generate swagger from tomcru cfg
                api.spec = self.p.serv('::eme2swagger').convert_to_swagger(api)

            sam_tpl['Resources'][api.api_name] = self.p.serv('aws:sam:spec_api_b').build_api(api, env)

        sam_tpl['Resources'].update(lambda_builder.build_layers())
        for lambda_id in lambda_builder.lambdas:
            sam_tpl['Resources'][lambda_id.replace('/', '_')] = lambda_builder.build_lambda(lambda_id, env=env)

        # add parameters
        sam_tpl['Parameters'].update(
            self.param_builder.build_params()
        )

        # sort template keys (preferred aws order)
        sam_tpl = self._sort_keys_tpl(sam_tpl)

        # now save SAM yaml to file
        with open(os.path.join(self.cfg.app_path, 'template.yaml'), 'w') as fh:
            yaml.dump(sam_tpl, stream=fh)
            print("Saved to template.yaml!")

    def run_apps(self):

        print("Deployment not supported yet")
        raise NotImplementedError()

    def build_app_stack(self, env):
        tpl = {
            'AWSTemplateFormatVersion': '2010-09-09',
            'Transform': 'AWS::Serverless-2016-10-31',
            # todo: add custom description
            'Description': 'Serverless website',
            'Parameters': {},
            'Globals': {},
            'Resources': {}
            # todo: output
        }

        # inject app parameters hier

        return tpl

    def _sort_keys_tpl(self, tpl):
        SAM_KEYS_ORDER = ['AWSTemplateFormatVersion', 'Transform', 'Description', 'Parameters', 'Globals', 'Resources']
        # RES_KEYS_ORDER = ['Type', 'Parameters']
        #
        tpl = {k: tpl[k] for k in sorted(tpl, key=lambda x: SAM_KEYS_ORDER.index(x) if x in SAM_KEYS_ORDER else 1000)}

        AWSSAM_RES_TYPE_ORDER = [
            'AWS::Serverless::LayerVersion',
            'AWS::Serverless::Function',
            'AWS::Serverless::HttpApi',
        ]

        SWAGGER_ORDER = [
            'openapi',
            'version',
            'info',
            'components',
            'paths'
        ]

        for k in list(tpl.keys()):
            if not tpl[k]:
                del tpl[k]

        return tpl
