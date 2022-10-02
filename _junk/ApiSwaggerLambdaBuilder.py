import os.path
import shutil
from typing import Dict

from tomcru import TomcruCfg, TomcruProject, TomcruApiDescriptor
from tomcru.core import utils


class ApiSwaggerLambdaBuilder:

    def __init__(self, project: TomcruProject, swagger_cfg):
        self.cfg: TomcruCfg = project.cfg
        self.p = project

        # params passed to Integrators:
        self.swagger_cfg = swagger_cfg

    def build_swagger_lambda(self, lambda_id, api: TomcruApiDescriptor):
        # generate swagger lambda files if they dont exist
        lambda_path = os.path.join(self.cfg.app_path, 'lambdas', lambda_id)

        if not os.path.exists(lambda_path):
            os.makedirs(lambda_path)

            basepath = os.path.dirname(os.path.realpath(__file__))

            shutil.copy2(
                os.path.join(basepath, 'src', 'SwaggerLambda.py'),
                os.path.join(lambda_path, 'app.py')
            )

        # copy swagger files
        #swagger_path = api.swagger_file
        shutil.copy(
            api.swagger_file,
            os.path.join(lambda_path, os.path.basename(api.swagger_file))
        )
