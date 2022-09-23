import asyncio
import uuid

from eme.websocket import WebsocketApp

from tomcru import TomcruCfg


class EmeWsApp(WebsocketApp):
    def __init__(self, tomcrucfg: TomcruCfg, cfg: dict):
        super().__init__({})

    def post_to_connection(self, ConnectionId, Data: str):
            # Data = json.loads(Data)

            # @todo: detect app type
            # if not isinstance(self.app, EmeSamWsApp):
            #     raise Exception("Not provided WS app as proxy! " + str(type(self.app)))

            if isinstance(ConnectionId, str):
                ConnectionId = uuid.UUID(ConnectionId)

            # todo: itT: find client wrapper by conn id
            client = self._clients[ConnectionId]

            asyncio.ensure_future(self.send(Data, client))
