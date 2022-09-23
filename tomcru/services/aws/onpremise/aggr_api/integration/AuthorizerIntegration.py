import json
import os

from eme.entities import EntityJSONEncoder

from flask import request

from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiLambdaAuthorizerDescriptor


class LambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, auth_cfg, lambda_builder):
        self.cfg = cfg
        self.lambda_builder = lambda_builder

    def get_authorizer_resp(self, evt: dict):
        user = None

        if not user:
            authorizer_name, authorizer_fn = self.authorizer
            auth_event = {
                'identitySource': event['headers'].get('authorization'),
                'headers': event['headers'].copy()
            }

            # set env variables
            if authorizer_name != '__MOCK__':
                lambda_builder.set_env_for(authorizer_name)

            # "set DEBUG=true"
            # call authorizer if not cached
            resp = authorizer_fn(auth_event, self)

            if resp.get('statusCode', 200) == 200:
                user = resp['context']
            elif resp.get('isAuthorized'):
                user = None

            if user:
                # @todo: cache authorizer response
                pass

        return user

    def parse_response(self, resp: dict):
        # parse response
        if isinstance(resp, dict):
            if 'body' in resp:
                body = json.dumps(resp['body'])
                statusCode = resp.get('statusCode', 200)
            else:
                body = json.dumps(resp, cls=EntityJSONEncoder)
                statusCode = 200
        else:
            body = resp
            statusCode = 200
            #body, statusCode = resp.get('body', ''), resp.get('statusCode', 200)

        return body, statusCode

    def get_called_lambda(self):
        lamb = request.endpoint
        lamb = lamb.split(':')[1] if ':' in lamb else lamb
        return lamb



class ExternalLambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):
    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, apigw_cfg: dict):
        self.cfg = cfg

        filepath = apigw_cfg['__authorizer_mock__'].get(cfg.auth_id)

        auth_resp_path = apigw_cfg['__fileloc__']
        with open(os.path.join(filepath, auth_resp_path)) as fh:
            self.auth_resp = json.load(fh)

    def get_authorizer_resp(self, event: dict):

        if self.auth_resp['isAuthorized']:
            event['requestContext']['authorizer'] = {
                'lambda': self.auth_resp['context'].copy()
            }

            return True
        return False
