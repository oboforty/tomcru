from tomcru import TomcruEndpointDescriptor, TomcruProject, TomcruLambdaIntegrationDescription


class LambdaBuilder:
    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.lambdas = set()
        self.layers = set()

        self.param_builder = project.serv('aws:sam:params_b')

    def build_lambda_globals(self):
        # todo: maybe use __default__ opts?

        return {
            'AutoPublishAlias': 'live',
            'Handler': 'app.handler',
            'Runtime': 'python3.10',
            'Timeout': 120,
            'MemorySize': 128,
            'Architectures': ['arm64']
        }

    def build_lambda(self, lambda_id, env):

        group, lamb = lambda_id.split('/')
        tpl = {
            'Type': 'AWS::Serverless::Function',
            'Properties': {
                'FunctionName': f'{group}_{lamb}',
                'CodeUri': f'./lambdas/{group}/{lamb}'
            }
        }

        # get envs
        _envs = self.cfg.envs[env]

        if lambda_id in _envs:
            tpl['Properties']['Environment'] = {
                'Variables': dict(_envs[lambda_id])
            }

        overrides = self.opts.get('__default__', {})
        overrides.update(self.opts.get(lambda_id, {}))

        # todo: more lambda settings & override globals too
        if 'exec_role' in overrides:
            tpl['Properties']['Role'] = self.param_builder.store('LambdaExecRole', overrides['exec_role'])


        return tpl

    def build_layers(self):
        layers = {}

        for (layer_name, _, _, _) in self.cfg.layers:
            layers[layer_name] = {
                'Type': 'AWS::Serverless::LayerVersion',
                'Properties': {
                    'LayerName': layer_name,
                    'ContentUri': f'./layers/{layer_name}.zip',
                    'CompatibleRuntimes': ['provided'],
                    #'LicenseInfo': 'Available under the MIT-0 license.'
                }
            }

        return layers

    def add_lambda(self, lambda_id):
        self.lambdas.add(lambda_id)
