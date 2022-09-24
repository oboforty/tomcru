from datetime import datetime
import inspect
import json
import os
import time

from eme.entities import load_handlers

from awssam.AwsSamCfg import AwsSamCfg
from ..services.apps.EmeSamWsApp import EmeSamWsApp


class WsProxyContextBuilder:

    def __init__(self, cfg: AwsSamCfg):
        self.apis = cfg.wss
        self.app = EmeSamWsApp(cfg)
        self.authorizer = None
        self.app_path = cfg.app_path
        self.type = 'ws'

    def get_event_and_context(self, groupHandler, group=None, route=None, msid=None, user=None, data=None, client=None, token=None, **kwargs):
        # get called lambda
        method_name = self.app._endpoints_to_methods[route].split(':')[1]
        group_id, lamb = route.split(self.app.route_sep)

        # set env variables
        client_info = self.app._client_infos[client.id]

        # fetch lambda from endpoint
        lamb_fn = groupHandler.methods[method_name]
        sig = inspect.signature(lamb_fn)

        # create ApiGw Websocket event
        # todo: handle these data from eme WS:
        stage = "production"
        identity = {}
        domain = "?"
        api_id = "?"
        methodArn = "??????????????:????"

        event = {
            'methodArn': methodArn,

            'requestContext': {
                "routeKey": route,
                "stage": stage,
                "apiId": api_id,

                'methodArn': methodArn,

                "eventType": "MESSAGE",
                "messageDirection": "IN",
                "messageId": msid,
                "extendedRequestId": msid,
                "requestId": msid,

                "connectionId": str(client.id),
                "connectedAt": client_info['connected_at'],

                "requestTimeEpoch": time.time(),
                "requestTime": datetime.utcnow().strftime("%d/%m/%Y:%H:%M:%S") + '+0000',
                "identity": identity,
                "domainName": domain,
            },
            'body': json.dumps({
                "group": group,
                "route": route,
                **vars(data)
            }),
            "isBase64Encoded": False
        }

        self.load_user(event, groupHandler.lambda_builder)

        # fake aws event & ctx
        _lam_arsg = []
        _lam_arsg.append(event)
        if len(sig.parameters) >= 2:
            _lam_arsg.append(groupHandler.lambda_builder.get_context())

        return lamb, lamb_fn, _lam_arsg

    async def prepare_response(self, body, statusCode):
        # empty route, no WS reply (not supported by AWS)

        return None

    def set_authorizer(self, authorizer_name, authorizer_fn):
        self.authorizer = authorizer_name, authorizer_fn

    def mock_authorizer(self, response):
        # hack for eme comma parser:
        if isinstance(response, list):
            response = ','.join(response)

        user = json.loads(response) if isinstance(response, str) else response

        authorizer_fn = lambda event, ctx: {
            "principalId": "me",
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if 'queryStringParameters' in event and 'authorization' in event['queryStringParameters'] else 'Deny',
                    "Resource": event['methodArn']
                }
            ],
            "context": user,
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
                "methodArn": event['methodArn'],
                'requestContext': event['requestContext'].copy(),
                'headers': event.get('headers', {}).copy(),
                'queryStringParameters': {
                    'authorization': event.get('queryStringParameters', {}).get('authorization'),
                }
            }

            # set env variables
            if authorizer_name != '__MOCK__':
                lambda_builder.set_env_for(authorizer_name)

            #"set DEBUG=true"
            # call authorizer if not cached
            resp = authorizer_fn(auth_event, self)

            if resp.get('Statement', [{}])[0].get('Effect') == 'Allow':
                user = resp['context']
            else:
                user = None

            if user:
                # @todo: cache authorizer response
                pass
        
        if user:
            # set lambda user context
            event['requestContext']['authorizer'] = {
                'lambda': user
            }

        return user

    def load_eme_handlers(self, groups):

    def add_method(self, endpoint, ):

    @property
    def route_collections(self):
        return self.apis.items()
