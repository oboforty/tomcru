import asyncio
import time
from types import SimpleNamespace
from typing import Dict


from tomcru import TomcruSubProjectCfg, TomcruApiDescriptor


class EmeWsApp(WebsocketApp):
    def __init__(self, wsappcfg: TomcruApiDescriptor, cfg: dict):
        self.debug = True
        self.api_name = wsappcfg.api_name
        self.api_type = 'ws'
        self.is_main_thread = False

        super().__init__({
            'websocket': {
                'type': 'samapp',
                'debug': True,
            }
        })
        self._clients: Dict[str, EmeWebsocketClient] = {}
        self._client_infos = {}
        self.boto3 = None
        self.port = cfg.get('port')

    def on_connect(self, client, path):
        self._clients[client.id] = client

        # todo: itt: handle authorizer lambdas

        self._client_infos[client.id] = {
            "connected_at": time.time()
        }

        # call $CONNECT endpoint lambda
        method = self._endpoints_to_methods["$connect"]
        fn, sig = self._methods[method]

        # run sync
        asyncio.ensure_future(fn(route='$connect', client=client, data=SimpleNamespace()))
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(coroutine)

    def on_disconnect(self, client, path):
        self._clients.pop(client.id, None)
        self._client_infos.pop(client.id, None)

        # todo call $DISCONNECT endpoint lambda

    def run(self, host=None, port=None, debug=None):
        if host:
            self.host = host
        if port:
            self.port = port
        if debug is not None:
            self.debug = debug

        self.start()

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

