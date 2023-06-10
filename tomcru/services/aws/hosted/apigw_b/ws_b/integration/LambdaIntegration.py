import inspect
import json
import time
from datetime import datetime
from urllib import parse

from tomcru import TomcruApiEP, TomcruLambdaIntegrationEP, TomcruEndpoint


class LambdaIntegration:

    def __init__(self, app, endpoint: TomcruLambdaIntegrationEP, lambda_builder):
        self.app = app
        self.auth_integ = app._integ_authorizer
        self.endpoint = endpoint
        self.lambda_builder = lambda_builder

        self.lambda_builder.build_lambda(endpoint.lambda_id)

    async def __call__(self, base_headers: dict = None, **kwargs):
        evt = self.get_event(**kwargs)

        assert self.auth_integ is not None

        # Api GW only authenticates at $connect, and its guaranteed to be cached afterwards
        if '$connect' == evt['requestContext']['routeKey']:
            _auth_ok = self.auth_integ.authorize(evt)
        else:
            _auth_ok = self.auth_integ.check_cached_auth(evt)

        if _auth_ok:
            resp = self.lambda_builder.run_lambda(self.endpoint.lambda_id, evt)

            return self.parse_response(resp)
        else:
            # todo: handle unauthenticated
            raise Exception("Authorizer refused")

    def get_event(self, client, route, data: object, group=None, msid=None, user=None, token=None, **kwargs):
        # get called lambda
        #method_name = self.app._endpoints_to_methods[route].split(':')[1]
        #group_id, lamb = route.split(self.app.route_sep) if '/' in route else None, route

        # set env variables
        client_info = self.app._client_infos[client.id]

        # create ApiGw Websocket event
        stage = "production"
        identity = {} #todo: client.local_address & etc
        domain = "?"
        methodArn = self.endpoint.lambda_id

        if route == "$connect": eventType = "CONNECT"
        elif route == "$disconnect": eventType = "DISCONNECT"
        else: eventType = "MESSAGE"

        event = {
            'methodArn': methodArn,
            'requestContext': {
                # client
                "connectionId": str(client.id),
                "connectedAt": client_info['connected_at'],

                # request
                "routeKey": route,
                "stage": stage,
                "apiId": self.app.api_name,
                'methodArn': methodArn,
                "eventType": eventType,
                "messageDirection": "IN",
                "messageId": msid,
                "extendedRequestId": msid,
                "requestId": msid,
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

        if eventType == "CONNECT":
            event['headers'] = dict(client.request_headers)
            event['queryStringParameters'] = dict(parse.parse_qsl(parse.urlsplit(client.path).query))

        return event

    def parse_response(self, content: dict):
        """
        Parses WS lambda integration's response to websocket response
        :param resp: lambda ws integration response
        :return: output_str
        """

        return content

    def __str__(self):
        return str(self.endpoint)

    def __repr__(self):
        return f'<{self.__class__.__name__} endpoint={self.endpoint}>'
