import json
import os
from collections import defaultdict

from eme.entities import EntityJSONEncoder

from flask import request

from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiLambdaAuthorizerDescriptor


class LambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, auth_cfg, lambda_builder, env=None):
        self.cfg = cfg
        self.lambda_builder = lambda_builder

        self.lambda_folder = cfg.lambda_source
        self.lambda_id = cfg.lambda_id
        self.env = env

        self.lambda_builder.build_lambda(self.lambda_id, env=self.env)

        self.authorizers_cache = {}

    def authorize(self, event: dict):
        auth_event = {
            'requestContext': event['requestContext'].copy(),
            'identitySource': event['headers'].get('authorization'),
            'headers': event['headers'].copy()
        }

        # check if cached
        cache_key = auth_event['identitySource']
        user = self.authorizers_cache.get(cache_key) if cache_key else None

        if not user:
            resp = self.lambda_builder.run_lambda(self.lambda_id, auth_event, self.env)

            if resp.get('statusCode', 200) == 200:
                user = resp['context']
            elif resp.get('isAuthorized'):
                user = None

                # todo: don't pass through? check aws docks
            if user:
                # cache authorizer response
                self.authorizers_cache[cache_key] = user

        if user:
            # integrate into event
            event['requestContext']['authorizer'] = {
                'lambda': user.copy()
            }

        return user


class ExternalLambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):
    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, apigw_cfg: dict):
        self.cfg = cfg

        group, lamb = cfg.lambda_id.split('/')

        auth_resp_path = apigw_cfg['__fileloc__']
        with open(os.path.join(auth_resp_path, lamb+'_mock.json')) as fh:
            self.auth_resp = json.load(fh)

    def authorize(self, event: dict):

        if self.auth_resp['isAuthorized']:
            event['requestContext']['authorizer'] = {
                'lambda': self.auth_resp['context'].copy()
            }

            return True
        return False
