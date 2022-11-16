import asyncio
import uuid


class ApiGWMgr:

    def __init__(self, project, opts):
        self.p = project
        self.ws = None
        self.http = None

    def init(self):
        objs = self.p.serv('aws:onpremise:obj_store')
        objs.add('boto3', 'apigatewaymanagementapi', self)

    def add_app(self, app):
        if 'ws' == app.api_type:
            self.ws = app
        elif 'http' == app.api_type:
            self.http = app

        # todo: store apps by their IDs, so that we can refer to this from apigatewaymanagement endpoint

    def post_to_connection(self, ConnectionId, Data: str):
        # Data = json.loads(Data)

        # @todo: detect app type
        # if not isinstance(self.app, EmeSamWsApp):
        #     raise Exception("Not provided WS app as proxy! " + str(type(self.app)))

        if isinstance(ConnectionId, str):
            ConnectionId = uuid.UUID(ConnectionId)

        # todo: itT: find client wrapper by conn id
        client = self.ws._clients[ConnectionId]

        asyncio.ensure_future(self.ws.send(Data, client))
