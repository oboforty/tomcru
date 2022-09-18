import json

from eme.entities import EntityJSONEncoder

from flask import request

from tomcru import TomcruApiDescriptor, TomcruLambdaIntegrationDescription


class LambdaIntegration:

    def __init__(self, api: TomcruApiDescriptor):
        self.endpoint = self.get_called_endpoint(api)

    def get_event(self, **kwargs):
        event = {
            'requestContext': {
                "http": {
                    "method": self.endpoint.method_name
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
                try:
                    body = json.dumps(resp['body'])
                except:
                    body = resp['body']
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
        """
        Gets called lambda ID
        :return:
        """
        ep = request.endpoint

        group, method_name = ep.split(':')
        method, lamb = method_name.split("_")

        return f'{group}/{lamb}'

    def get_called_endpoint(self, api: TomcruApiDescriptor) -> TomcruLambdaIntegrationDescription:
        """
        Gets called endpoint in Tomcru cfg descriptors
        :return:
        """
        route = api.routes[str(request.url_rule)]
        endpoint = next(filter(lambda x: x.endpoint_id == request.endpoint, route.endpoints), None)

        # todo: handle multiple integration types
        assert isinstance(endpoint, TomcruLambdaIntegrationDescription)

        return endpoint
