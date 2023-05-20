from flask import request, Response, jsonify

from tomcru.services.aws.hosted.apigw.api_shared.integration import TomcruApiGWHttpIntegration, \
    LambdaAuthorizerIntegration
from tomcru import TomcruApiEP, TomcruLambdaIntegrationEP, TomcruEndpoint


class LambdaIntegration(TomcruApiGWHttpIntegration):

    def __init__(self, endpoint: TomcruLambdaIntegrationEP, auth: LambdaAuthorizerIntegration, lambda_builder, env=None):
        self.endpoint = endpoint
        self.auth_integ = auth
        self.lambda_builder = lambda_builder
        self.env = env

        self.lambda_builder.build_lambda(endpoint.lambda_id)

    def on_request(self, base_headers: dict, **kwargs):
        evt = self.get_event(**kwargs)

        if not self.auth_integ or self.auth_integ.authorize(evt):
            resp = self.lambda_builder.run_lambda(self.endpoint.lambda_id, evt)

            return self.parse_response(resp, base_headers=base_headers)
        else:
            # todo: handle unauthenticated
            raise Exception("Authorizer refused")

    def get_event(self, **kwargs):
        route_key = f'{self.endpoint.method} {self.endpoint.route}'

        event = {
            'version': '2.0',
            'routeKey': route_key,
            'rawQueryString': request.query_string.decode('utf8'),
            'requestContext': {
                "protocol": "HTTP/1.1",
                #"httpMethod": self.endpoint.method,
                "http": {
                    "method": self.endpoint.method,
                    "routeKey": route_key
                },
            },
            'body': request.data.decode('utf8'),
            'queryStringParameters': dict(request.args),
            'headers': dict((k.lower(), v) for k, v in request.headers.items()),
            'pathParameters': dict(request.view_args) | kwargs
        }

        # apply request parameters transformation
        if hasattr(self.endpoint, 'integ_opts') and 'requestParameters' in self.endpoint.integ_opts:
            for id_to, id_from in self.endpoint.integ_opts['requestParameters'].items():
                if id_from.startswith('query'): src_from = event['queryStringParameters']
                elif id_from.startswith('headers'): src_from = event['headers']
                elif id_from.startswith('body'): src_from = event['body']
                elif id_from.startswith('path'): src_from = event['pathParameters']
                else: raise Exception(id_from)

                if id_to.startswith('query'): src_to = event['queryStringParameters']
                elif id_to.startswith('headers'): src_to = event['headers']
                elif id_to.startswith('body'): src_to = event['body']
                elif id_to.startswith('path'): src_to = event['pathParameters']
                else: raise Exception(id_to)

                # todo: process list
                args_from = next(iter(id_from.split('.')[1:]))
                args_to = next(iter(id_to.split('.')[1:]))

                if args_from in src_from:
                    src_to[args_to] = src_from[args_from]

        return event

    def parse_response(self, content: dict, base_headers: dict):
        """
        Parses HTTP lambda integration's response to flask response
        :param resp: lambda integration response (2.0 format)
        :return: output_str, status_code
        """
        headers = base_headers.copy()
        resp: Response

        # parse response
        if isinstance(content, dict):
            if 'body' in content:
                resp = Response(str(content['body']), status=content.get('statusCode', 200))
                headers.update(content.get('headers', {}))
            else:
                resp = jsonify(content)
                resp.status = 200
        else:
            resp = Response(content, status=200)

        resp.headers = headers
        resp.cookies = None

        return resp
