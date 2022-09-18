import json
from eme.entities import EntityJSONEncoder

from flask import request


class LambdaIntegration:

    def get_event(self, **kwargs):
        lamb = self.get_called_lambda()
        method = lamb.split('_')[0]

        event = {
            'requestContext': {
                "http": {
                    "method": method
                },
            },
            'body': request.data,
            'queryStringParameters': dict(request.args),
            'headers': dict((k.lower(), v) for k, v in request.headers.items())
        }
        # merge url params into query params:
        event['queryStringParameters'].update(kwargs)

        return event

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
