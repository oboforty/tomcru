import os
import json

from tomcru import TomcruApiDescriptor, TomcruProject

from flask import Flask, request, jsonify


class MockedApiBuilder:

    def __init__(self, project: TomcruProject, mock_cfg):
        self.cfg = project.cfg
        self.p = project
        self.mock_cfg = self.p.load_serv_cfg('aws:onpremise:aggr_api')

        self.env: str = None
        self.resp = None

    def build_api(self, api: TomcruApiDescriptor, env: str):
        self.env = env

        api_cfg = self.mock_cfg['__default__'].copy()
        api_cfg.update(self.mock_cfg[api.api_name])

        response_file = api_cfg.get('response_file', api.default_authorizer)

        with open(os.path.join(self.mock_cfg['__fileloc__'], response_file+'.json')) as fh:
            self.resp = json.load(fh)

        app = MockApi(self.resp, __name__)

        # setup conf for app runner
        app.api_name = api.api_name
        app.is_main_thread = False
        app.host = api_cfg.get('host', 'localhost')
        app.port = api_cfg.get('port', 5000)

        return app
