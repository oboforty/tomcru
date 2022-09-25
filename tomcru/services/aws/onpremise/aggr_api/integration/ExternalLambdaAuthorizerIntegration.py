import json
import os

from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiLambdaAuthorizerDescriptor


class ExternalLambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):
    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, apigw_cfg: dict):
        super().__init__(cfg)
        self.cfg = cfg

        group, lamb = cfg.lambda_id.split('/')

        auth_resp_path = apigw_cfg['__fileloc__']
        with open(os.path.join(auth_resp_path, lamb+'_mock.json')) as fh:
            self.auth_resp = json.load(fh)

    def authorize(self, event: dict, source=None):

        if self.auth_resp['isAuthorized']:
            event['requestContext']['authorizer'] = {
                'lambda': self.auth_resp['context'].copy()
            }

            return True
        return False
