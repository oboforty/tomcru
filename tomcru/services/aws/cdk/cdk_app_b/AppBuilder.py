import aws_cdk

import logging
import os.path

from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class AppBuilder(ServiceBase):
    INIT_PRIORITY = 1

    cdk = aws_cdk
    app: cdk.App
    stacks: dict[str, cdk.Stack]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stacks = {}

    def inject_dependencies(self):
        pass

    def init(self):
        self.app = self.cdk.App()
        self.env = self.cdk.Environment(**self.opts.get('environment'))

        for stack_cfg in self.opts.get('stacks'):
            stid = stack_cfg['id']
            self.stacks[stid] = self.cdk.Stack(self.app, id=stid, env=self.env)

    def synth(self):
        self.app.synth()

    def deploy(self):
        pass
