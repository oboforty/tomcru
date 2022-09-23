import json
import os

from eme.entities import load_handlers
from flask import request
import inspect

from awssam.AwsSamCfg import AwsSamCfg
from ..services.apps.EmeSamWebApp import EmeSamWebApp
from ..services.controllers.HomeController import HomeController


class HttpProxyContextBuilder:

    def __init__(self, cfg: AwsSamCfg):
        self.apis = cfg.apis
        self.app = EmeSamWebApp(cfg)
        self.authorizer = None
        self.app_path = cfg.app_path
        self.type = 'http'

    def set_authorizer(self, authorizer_name, authorizer_fn):
        self.authorizer = authorizer_name, authorizer_fn

    def mock_authorizer(self, response):
        user = json.loads(response) if isinstance(response, str) else response

        authorizer_fn = lambda event, ctx: {
            "isAuthorized": True,
            "context": user
        }

        self.authorizer = '__MOCK__', authorizer_fn

    def load_user(self, event, lambda_builder):
        if not self.authorizer:
            return None

        # @todo: get from cache
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

            #"set DEBUG=true"
            # call authorizer if not cached
            resp = authorizer_fn(auth_event, self)

            if resp.get('statusCode', 200) == 200:
                user = resp['context']
            elif resp.get('isAuthorized'):
                user = None

            if user:
                # @todo: cache authorizer response
                pass

        # user is either cached or from authorizer
        if user:
            # set lambda user context
            event['requestContext']['authorizer'] = {
                'lambda': user
            }

        return user

    def add_method(self, endpoint, lambda_fn):
        # replace AWS APIGW route scheme to flask routing schema
        _api_route = endpoint.route.replace('{', '<').replace('}', '>')
        self.app._custom_routes[endpoint.endpoint_id].add(_api_route)

    @property
    def route_collections(self):
        return self.apis.items()
