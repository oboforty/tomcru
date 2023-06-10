import inspect
import json
import signal
import time
from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace
import asyncio
import logging
import sys
from os.path import join

import websockets
from websockets.connection import State


CTRL_ATTRIBUTES = ['server', 'app']


class WsClient(websockets.WebSocketServerProtocol):
    token = None
    user = None
    room_id = None


class RouteNotFoundError(Exception):
    pass


class RouteForbiddenError(Exception):
    pass


class WebsocketApp:
    def __init__(self, conf: dict):
        # Socket
        self.host = conf.get('host', '0.0.0.0')
        self.port = conf.get('port', 3000)
        self.route_sep = '/'
        self.route_getter = lambda x: x.pop('route', None)

        # Flags
        self.debug = conf.get('debug')

        # ws handlers
        self._endpoints_to_methods = {}
        self._methods = {}

        self._clients: dict[str, WsClient] = {}
        self._client_infos = {}

        signal.signal(signal.SIGINT, self.close_sig_handler)

        if conf.get('rooms'):
            self.rooms = defaultdict(set)
        else:
            self.rooms = None

    def close_sig_handler(self, signal, frame):
        self.close()

    async def handle_requests(self, websocket, path):
        self.on_connect(websocket, path)

        try:
            async for message in websocket:
                rws = json.loads(message)

                # get action
                route = self.route_getter(rws) or self.route_sep
                group, method = route.split(self.route_sep)
                msid = rws.pop('msid', None)

                # check if action is valid
                if route not in self._endpoints_to_methods:
                    if self.debug:
                        print(f"  [{datetime.now()}] {msid} {route} - 404")
                    return  # todo: return with error?

                # @TODO: itt: websocket has no user and token (it's not that class!)
                # @todo:   how to inject token as authenticate?

                # Build request
                method_id = self._endpoints_to_methods[route]
                action, sig = self._methods[method_id]

                params = {}
                if 'msid' in sig: params['msid'] = msid
                if 'user' in sig: params['user'] = websocket.user
                if 'client' in sig: params['client'] = websocket
                if 'token' in sig: params['token'] = websocket.token
                if 'data' in sig: params['data'] = SimpleNamespace(**rws)
                if 'route' in sig: params['route'] = route

                # Execute request & send response
                if self.debug:
                    print(f"  [{datetime.now()}] {msid} {route}")

                try:
                    response = await action(**params)

                    if response is not None:
                        await self.send(response, websocket, route=route, msid=msid)
                except RouteNotFoundError:
                    if self.debug:
                        print(f"  [{datetime.now()}] {msid} {route} - 404")
                except RouteForbiddenError:
                    if self.debug:
                        print(f"  [{datetime.now()}] {msid} {route} - 403")
                except Exception as e:
                    logging.exception("METHOD")

                    if self.debug:
                        raise e
        except websockets.exceptions.ConnectionClosedError:
            self.on_disconnect(websocket, path)

    async def send(self, rws, client: WsClient, route=None, msid=None):
        if client.state is State.CLOSED:
            return

        if isinstance(rws, dict):
            if route is not None:
                rws['route'] = route

            if msid is not None:
                rws['msid'] = msid

            await client.send(json.dumps(rws))
        elif isinstance(rws, str):
            await client.send(rws)
        elif isinstance(rws, list):
            for rw_ in rws:
                await self.send(rw_, client, route=route)
        else:
            raise Exception("Unsupported message type: {}".format(type(rws)))

    async def send_to_room(self, rws, room_id=None, client=None):
        if room_id is None and client is not None:
            room_id = client.room_id
        elif self.rooms is None:
            raise Exception("send_to_room was called but rooms are not configured in this app")

        room_client: WsClient
        for room_client in self.rooms[room_id]:
            if room_client.state == State.OPEN:
                await self.send(rws, room_client)

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


    async def send_broadcast(self, rws):
        for room_id in self.rooms:
            await self.send_to_room(rws, room_id)

    def close(self):
        print("Exited websocket server")
        sys.exit()

    # def init_modules(self, modules, webconf):
    #     for module in modules:
    #         module.init_dal()
    #
    #         if hasattr(module, 'init_wsapp'):
    #             module.init_wsapp(self, webconf)

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

    def run(self, host=None, port=None, debug=None, threaded=None):
        if host:
            self.host = host
        if port:
            self.port = port
        if debug is not None:
            self.debug = debug

        print("Websocket: listening on {}:{}".format(self.host, self.port))

        asyncio.get_event_loop().run_until_complete(websockets.serve(self.handle_requests, self.host, self.port, klass=WsClient))
        asyncio.get_event_loop().run_forever()

    def preset_endpoint(self, route_key, endpoint):
        # strip the verb from the url
        sp = route_key.split(' ')
        prefix = 'WS' if len(sp) == 1 else sp[0].upper()
        route_key = ''.join(sp[1:])

        # force the GET keyword into the endpoint
        controller, method = endpoint.split(':')
        if prefix == 'WS' and method[0:2].lower() != 'ws':
            method = prefix.lower() + '_' + method

        # custom routes are a map of {Controller.verb_method -> overridden_url}
        endpoint = controller + self.route_sep + method
        self._endpoints_to_methods[route_key] = endpoint

    def preset_endpoints(self, rules):
        for route_key, endpoint in rules.items():
            self.preset_endpoint(route_key, endpoint)

    def load_groups(self, groups, conf):
        if not groups: return
        # Similar to WebApp's load_controllers
        debug_len = conf.get('__debug_len__', 20)

        # todo: later: override by presets (like in webapp)
        print(('\n{0: <' + str(debug_len) + '}{1}').format('ROUTE', 'ENDPOINT'))

        covered_methods = set(self._endpoints_to_methods.values())

        for group_name, group in groups.items():
            for method_name in dir(group):
                if method_name.startswith("_") or method_name in CTRL_ATTRIBUTES:
                    continue
                method = getattr(group, method_name)
                if not callable(method):
                    continue

                if not hasattr(group, 'group'):
                    group.group = group_name
                if not hasattr(group, 'route'):
                    group.route = group.group.lower()

                method_id = f'{group_name}:{method_name}'

                # discover signature - what the function requires
                sig = list(inspect.signature(method).parameters.keys())
                self._methods[method_id] = (method, sig)

                if method_id not in covered_methods:
                    # if custom URL(=routekey) mapping hasn't been found, generate a route
                    route = f'{group.route}{self.route_sep}{method_name}'
                    self._endpoints_to_methods[route] = method_id
                else:
                    route = list(self._endpoints_to_methods.keys())[list(self._endpoints_to_methods.values()).index(method_id)]

    def debug_groups(self, conf):
        debug_len = conf.get('__debug_len__', 20)

        for route, method_id in self._endpoints_to_methods.items():
            _, sig = self._methods[method_id]

            print(('{0: <' + str(debug_len) + '}{1:<10}').format(route, method_id, ','.join(sig)))
