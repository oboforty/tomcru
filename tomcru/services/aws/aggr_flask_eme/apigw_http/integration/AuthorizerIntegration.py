import json
from eme.entities import EntityJSONEncoder

from flask import request


class AuthorizerIntegration:

    def get_authorizer_event_and_execute_lambda(self, event, lambda_builder):
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

    def inject_event(self, event: dict, auth_resp: dict):

        if auth_resp['isAuthorized']:
            event['requestContext']['authorizer'] = {
                'lambda': auth_resp['context'].copy()
            }
