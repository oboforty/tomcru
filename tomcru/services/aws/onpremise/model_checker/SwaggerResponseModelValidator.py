import os
import json

from tomcru import TomcruApiDescriptor, TomcruProject, TomcruEndpointDescriptor, TomcruSwaggerIntegrationDescription

from flask import Flask, request, jsonify, Response, Request


class SwaggerResponseModelValidator:

    def __init__(self, project: TomcruProject, mock_cfg):
        self.cfg = project.cfg
        self.p = project

    def check_response(self, api: TomcruApiDescriptor, ep: TomcruEndpointDescriptor, response: Response, env: str):
        if isinstance(ep, TomcruSwaggerIntegrationDescription):
            # ignore all swagger endpoints, no need to validate
            return

        content_type = response.headers['content-type']
        _paths = api.spec_resolved_schemas['paths']

        if ep.route not in _paths:
            self.log_warning("Not in paths")

        ep_model = _paths[ep.route][ep.method.lower()]

        req_model = ep_model['parameters']
        self._validate_request(request, req_model)

        resp_model = ep_model['responses'].get(str(response.status_code), 'default')
        schema_model = resp_model['content'][content_type]['schema']
        header_model = resp_model.get('headers', {})
        self._validate_response(response, schema_model, header_model)

    def _validate_request(self, req: Request, parameters: list):

        for param in parameters:
            if not param.get('required', False):
                continue

            if 'path' == param['in']: act_in = dict(request.view_args)
            elif 'query' == param['in']: act_in = dict(req.args)
            elif 'header' == param['in']: act_in = dict(req.headers)
            elif 'cookie' == param['in']: act_in = dict(req.cookies)
            elif 'body' == param['in']: act_in = dict(req.json)
            else:
                raise NotImplementedError()

            if param['name'] not in act_in:
                # todo: not exception, but list of notifications somewhere
                raise Exception("fos")
                #print(param['name'], act_in)

            if 'schema' in param:
                req_model = param['schema']
                value = act_in[param['name']]

                if 'string' == req_model['type']: type_in = str
                elif 'integer' == req_model['type']: type_in = int
                elif 'number' == req_model['type']: type_in = float
                elif 'boolean' == req_model['type']: type_in = bool
                elif 'array' == req_model['type']: type_in = list
                elif 'object' == req_model['type']: type_in = object
                else:
                    # todo oneOf:
                    #   - type: string
                    #   - type: integer
                    raise NotImplementedError()

                if not isinstance(value, type_in):
                    # todo: not exception, but list of notifications somewhere
                    raise Exception("fos")

                # todo: minimum ≤ value ≤ maximum
                # todo: multipleOf
                # todo: str: minLength: 3
                #   - maxLength: 20
                # todo:   pattern: '^\d{3}-\d{2}-\d{4}$'
                # todo: nullable: true
                # https://swagger.io/docs/specification/data-models/data-types/

    """
    path parameters, such as /users/{id}
    query parameters, such as /users?role=admin
    header parameters, such as X-MyHeader: Value
    cookie parameters, which are passed in the Cookie header, such as Cookie: debug=0; csrftoken=BUSe35dohU3O1MZvDCU
    """

    def _validate_response(self, resp: Response, exp_resp: dict, exp_headers: dict):
        return
        header_model = header['schema']

        asdasd = {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['id', 'name'],
                'properties': {
                    'id': {'type': 'integer', 'format': 'int64'},
                    'name': {'type': 'string'},
                    'tag': {'type': 'string'}
                }
            }
        }

    def log_warning(self, err):
        print(err)
