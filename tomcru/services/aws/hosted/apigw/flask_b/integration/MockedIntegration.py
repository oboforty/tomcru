import json

from flask import request, jsonify, Response

from .LambdaIntegration import LambdaIntegration
from tomcru import TomcruMockedIntegrationEP
from tomcru.services.aws.hosted.apigw.api_shared.integration.TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration


from tomcru_jerry.mockapi import transform_response


base_headers = {
    "Content-Type": "application/json"
}


class MockedIntegration(LambdaIntegration):

    def __init__(self, endpoint: TomcruMockedIntegrationEP, auth: TomcruApiGWAuthorizerIntegration, response: dict, env=None):
        self.endpoint = endpoint
        self.auth_integ = auth
        self.env = env

        self.response = response

    def on_request(self, base_headers: dict, **kwargs):
        evt = self.get_event(**kwargs)

        if not self.auth_integ or self.auth_integ.authorize(evt):
            resp_tpl = self.response

            req = {
                'headers': {k.lower(): v for k, v in request.headers.items()},
                'params': dict(request.args),
            }

            if request.method != 'GET':
                req['body'] = request.get_json()

            if 'body' not in resp_tpl:
                resp_tpl['body'] = {}
            if 'headers' not in resp_tpl:
                resp_tpl['headers'] = {}

            resp2, status = transform_response(resp_tpl, req)
            resp2['headers'].update(base_headers)

            if isinstance(resp2['body'], (str, float, int)):
                r = Response(resp2['body'])
            else:
                r = jsonify(resp2['body'])

            if 'headers' in resp2:
                r.headers.update(resp2['headers'])
            r.status = status

            return r
        else:
            # todo: handle unauthenticated
            raise Exception("Authorizer refused")
