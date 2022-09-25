import inspect
import json
import time
from datetime import datetime


from tomcru import TomcruApiDescriptor, TomcruLambdaIntegrationDescription, TomcruEndpointDescriptor

from .TomcruApiGWWsIntegration import TomcruApiGWWsIntegration


class LambdaIntegration(TomcruApiGWWsIntegration):

    def __init__(self, wsapp, endpoint: TomcruLambdaIntegrationDescription, auth, lambda_builder, env=None):
        self.app = wsapp
        self.endpoint = endpoint
        self.auth_integ = auth
        self.lambda_builder = lambda_builder
        self.env = env

        self.lambda_builder.build_lambda(endpoint.lambda_id, env=self.env)

    def on_request(self, **kwargs):
        evt = self.get_event(**kwargs)

        if not self.auth_integ or self.auth_integ.authorize(evt, source='params'):
            resp = self.lambda_builder.run_lambda(self.endpoint.lambda_id, evt, self.env)

            return self.parse_response(resp)
        else:
            # todo: handle unauthenticated
            pass
            raise Exception("asdasd")

    def get_event(self, group=None, route=None, msid=None, user=None, data=None, client=None, token=None, **kwargs):
        # get called lambda
        method_name = self.app._endpoints_to_methods[route].split(':')[1]
        #group_id, lamb = route.split(self.app.route_sep) if '/' in route else None, route

        # set env variables
        client_info = self.app._client_infos[client.id]

        # create ApiGw Websocket event
        # todo: handle these data from eme WS:
        stage = "production"
        identity = {}
        domain = "?"
        api_id = self.app.api_name
        methodArn = self.endpoint.lambda_id

        if route == "$connect": eventType = "CONNECT"
        elif route == "$disconnect": eventType = "DISCONNECT"
        else: eventType = "MESSAGE"

        # TODO: $ITT: call authorizer, with $connect integration
        # todo: $ITT: get cached authorizer response?

        event = {
            'methodArn': methodArn,

            'requestContext': {
                "routeKey": route,
                "stage": stage,
                "apiId": api_id,

                'methodArn': methodArn,

                "eventType": eventType,
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
            # 'queryStringParameters': dict(request.args),
            # 'headers': dict((k.lower(), v) for k, v in request.headers.items())
            'body': json.dumps({
                "group": group,
                "route": route,
                **vars(data)
            }),
            "isBase64Encoded": False
        }

        return event

    def parse_response(self, resp: dict):
        """
        Parses WS lambda integration's response. EME can return responses as 1 on 1
        :param resp: lambda integration response (2.0 format)
        :return: output_str, status_code
        """

        return None
