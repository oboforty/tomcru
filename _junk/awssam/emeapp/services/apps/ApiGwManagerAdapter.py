import json
import uuid
import asyncio

from .EmeSamWebApp import EmeSamWebApp
from .EmeSamWsApp import EmeSamWsApp


class ApiGwManagerAdapter:
    def __init__(self, app):
        self.app = app
        self.endpoint_url = None

    def asd(self):
        if isinstance(self.app, EmeSamWebApp):
            pass
        elif isinstance(self.app, EmeSamWsApp):
            pass

    def post_to_connection(self, ConnectionId, Data: str):
        #Data = json.loads(Data)

        if not isinstance(self.app, EmeSamWsApp):
            raise Exception("Not provided WS app as proxy! " + str(type(self.app)))

        if isinstance(ConnectionId, str):
            ConnectionId = uuid.UUID(ConnectionId)

        # todo: itT: find client wrapper by conn id
        client = self.app._clients[ConnectionId]

        asyncio.ensure_future(self.app.send(Data, client))
