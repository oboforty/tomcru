import json

from eme.entities import EntityJSONEncoder

from flask import request

from tomcru import TomcruApiDescriptor, TomcruLambdaIntegrationDescription, TomcruEndpointDescriptor

from .TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration
from .AuthorizerIntegration import LambdaAuthorizerIntegration


class LambdaIntegration(TomcruApiGWHttpIntegration):

    def __init__(self, endpoint: TomcruLambdaIntegrationDescription, auth: LambdaAuthorizerIntegration, lambda_builder, env=None):
        self.endpoint = endpoint
        self.auth_integ = auth
        self.lambda_builder = lambda_builder
        self.env = env

        self.lambda_builder.build_lambda(endpoint.lambda_id, env=self.env)

    def on_request(self, **kwargs):
        evt = self.get_event(**kwargs)

        # @todo: cache authorizer response
        if self.auth_integ.authorize(evt):
            resp = self.lambda_builder.run_lambda(self.endpoint.lambda_id, evt, self.env)

            return self.parse_response(resp)
        else:
            # todo: handle unauthenticated
            pass
            raise Exception("asdasd")

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
        """
        Parses WS lambda integration's response. EME can return responses as 1 on 1
        :param resp: lambda integration response (2.0 format)
        :return: output_str, status_code
        """

        return None
