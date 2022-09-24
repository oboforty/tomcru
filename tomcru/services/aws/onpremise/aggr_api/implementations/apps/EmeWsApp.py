import asyncio
import uuid

from eme.websocket import WebsocketApp

from tomcru import TomcruCfg


class EmeWsApp(WebsocketApp):
    def __init__(self, tomcrucfg: TomcruCfg, cfg: dict):
        self.debug = True

        super().__init__({
            'websocket': {
                'type': 'samapp',
                'debug': True,
            }
        })
        self._clients = {}
        self._client_infos = {}
        self.boto3 = None

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

    def on_connect(self, client, path):
        self._clients[client.id] = client

        # todo: itt: handle authorizer lambdas

        self._client_infos[client.id] = {
            "connected_at": time.time()
        }

        # todo call $CONNECT endpoint lambda

    def on_disconnect(self, client, path):
        self._clients.pop(client.id, None)
        self._client_infos.pop(client.id, None)

        # todo call $DISCONNECT endpoint lambda

    # def get_clients_at(self, wid: str):
    #     for client in self.world_clients[str(wid)]:
    #         yield client
    #
    # async def send_to_world(self, wid: str, rws: dict, route=None, msid=None, isos=None):
    #     clients = self.world_clients.get(str(wid))
    #
    #     if clients:
    #         if isos is not None:
    #             for client in clients:
    #                 if client.user and client.user.iso in isos:
    #                     await self.send(rws, client)
    #         else:
    #             for client in clients:
    #                 await self.send(rws, client, route=route, msid=msid)

    # start threads
    # for tname, tcontent in self.threads.items():
    #     thread = threading.Thread(target=tcontent.run)
    #     thread.start()

    # def do_reconnect(self, client):
    #     if not client.user:
    #         return
    #
    #     # remove redundant old clients by the same user
    #     if client.user.wid:
    #         clients = self.onlineMatches[str(client.user.wid)]
    #
    #         for cli in list(clients):
    #             if cli == client:
    #                 # my current client, skip
    #                 continue
    #
    #             if cli.user and cli.user.uid == client.user.uid:
    #                 # client has the same uid, but is not my current client
    #                 # -> remove it
    #                 #print("Reconnect: ", cli.id, '->', client.id)
    #                 clients.remove(cli)
    #
    #     if client.user.wid:
    #         self.client_enter_world(client)
    #     else:
    #         self.onlineMatches[str(client.user.wid)].add(client)

