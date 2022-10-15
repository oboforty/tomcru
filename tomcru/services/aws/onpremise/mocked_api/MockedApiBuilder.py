import os
import json

from tomcru import TomcruApiDescriptor, TomcruProject

from eme.mockapi import MockApi
from flask import Flask, request, jsonify


class MockedApiBuilder:

    def __init__(self, project: TomcruProject, mock_cfg):
        self.cfg = project.cfg
        self.p = project
        self.mock_cfg = self.p.load_serv_cfg('aws:onpremise:aggr_api')

        self.env: str = None

    def build_api(self, api: TomcruApiDescriptor, env: str):
        self.env = env

        api_cfg = self.mock_cfg['__default__'].copy()
        api_cfg.update(self.mock_cfg[api.api_name])

        authorizer_mock = api_cfg.get('for_authorizer', api.default_authorizer)

        with open(os.path.join(self.mock_cfg['__fileloc__'], authorizer_mock+'_apimock.json')) as fh:
            self.resp = json.load(fh)

        app = MockApi(self.resp, __name__)

        # setup conf for app runner
        app.api_name = api_name
        app.is_main_thread = False
        app.host = api_cfg.get('host', 'localhost')
        app.port = api_cfg.get('port', 5000)

        return app

    def mock_server_builder(self, api_name):
        #
        # app = Flask()
        # app.api_name = api_name
        # app.is_main_thread = False
        #
        # @app.route('/oauth/me')
        # def authorizer_resp():
        #     if 'authorization' not in request.headers:
        #         return jsonify({}), 403
        #
        #     tk = request.headers['authorization']
        #
        #     if 'Bearer' in tk:
        #         tk = tk.split(' ')[1]
        #
        #     for k in list(self.resp.keys()):
        #         if isinstance(self.resp[k], str):
        #             self.resp[k] = self.resp[k].replace('{echo_token}', tk)
        #
        #     return jsonify(self.resp)

        return app
