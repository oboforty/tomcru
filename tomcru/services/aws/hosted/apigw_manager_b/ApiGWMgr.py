import asyncio
import uuid

from tomcru.services.ServiceBase import ServiceBase


class ApiGWMgr(ServiceBase):
    INIT_PRIORITY = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.conn = {}

    def init(self):
        self.service('boto3').add_resource('apigatewaymanagementapi', self)

    def add_app(self, app, ConnectionId):
        self.conn[ConnectionId] = app

    def post_to_connection(self, ConnectionId, Data: str):
        # if isinstance(ConnectionId, str):
        #     ConnectionId = uuid.UUID(ConnectionId)
        # Data = json.loads(Data)

        app = self.conn[ConnectionId]

        # todo: find client wrapper by conn id
        #       this'll need str -> uuid conversion!!!!!
        client = app._clients[ConnectionId]

        asyncio.ensure_future(app.send(Data, client))
