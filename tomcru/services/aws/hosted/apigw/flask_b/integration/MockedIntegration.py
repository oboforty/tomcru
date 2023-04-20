import json

from flask import request, Response, jsonify

from .LambdaIntegration import LambdaIntegration
from tomcru import TomcruMockedIntegrationDescription
from tomcru.services.aws.hosted.apigw.api_shared.integration.TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration


from tomcru_jerry.mockapi import transform_response


base_headers = {
    "content-type": "application/json"
}


class MockedIntegration(LambdaIntegration):

    def __init__(self, endpoint: TomcruMockedIntegrationDescription, auth: TomcruApiGWAuthorizerIntegration, filename: str, env=None):
        self.endpoint = endpoint
        self.auth_integ = auth
        self.env = env
        self.resp_tpls = {}

        # todo: support yaml & toml for mocked api?
        with open(filename) as fh:
            response = json.load(fh)

        self.resp_tpls[endpoint.endpoint_id] = response

    def on_request(self, **kwargs):
        evt = self.get_event(**kwargs)

        if not self.auth_integ or self.auth_integ.authorize(evt):
            ep_id = request.endpoint
            resp_tpl = self.resp_tpls[ep_id]

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

            r = jsonify(resp2['body'])
            if 'headers' in resp2:
                r.headers.update(resp2['headers'])
            r.status = status

            return r
        else:
            # todo: handle unauthenticated
            raise Exception("Authorizer refused")
