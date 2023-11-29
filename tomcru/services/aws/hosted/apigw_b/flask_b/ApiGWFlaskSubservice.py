import json
import os.path
import re
import logging
from typing import Callable

from flask import request, Flask, jsonify, send_from_directory, g, current_app

from tomcru_jerry import flask_jerry_setup, print_endpoints
from tomcru_jerry.controllers import add_endpoint
from tomcru_jerry.control import cors

from tomcru import \
    TomcruApiEP, TomcruEndpoint, TomcruRouteEP, \
    TomcruLambdaIntegrationEP, TomcruSwaggerIntegrationEP, TomcruMockedIntegrationEP,\
    TomcruAwsExposedApiIntegration, \
    TomcruApiAuthorizerEP, TomcruApiLambdaAuthorizerEP, TomcruApiOIDCAuthorizerEP
from tomcru.services.aws.hosted.apigw_b.ApiGWSubserviceBase import ApiGWSubserviceBase
from .integration import \
    LambdaIntegration, SwaggerIntegration, MockedIntegration,\
    aws_integ
from .authorizers import \
    LambdaAuthorizerIntegration, OIDCAuthorizerIntegration

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class ApiGWFlaskSubservice(ApiGWSubserviceBase):
    # transforms greedy path rules between AWS and Flask
    rgx_greedy_path_a2f = re.compile(r'\{([\w\d_]*)\+\}')
    rgx_greedy_path_f2a = re.compile(r'<path:([\w\d_]*)>')

    def create_app(self, api: TomcruApiEP, apiopts: dict):
        port = apiopts.get('port', 5000)

        api_id = f'{api.api_name}:{port}'
        app = Flask(api_id)

        # set custom attributes
        app.api_name = api_id
        app.api_type = 'http'
        app.is_main_thread = apiopts.get('main_api', False)

        return app

    def build_api(self, api: TomcruApiEP, apiopts: dict):
        conn_id = api.api_name
        self.service('apigw_manager').add_app(self, conn_id)

        self._build_authorizers()
        self._build_acl(api, apiopts.get('cors'))
        index = self._build_integrations(api, apiopts)

        self._build_extra_route_handlers(api, index)

    def _build_authorizers(self):
        # build authorizers
        for authorizer_id, auth in self.authorizers.items():
            if isinstance(auth, TomcruApiLambdaAuthorizerEP):
                # evaluate lambda sub type
                if 'external' == auth.lambda_source:
                    raise NotImplementedError("__fileloc__")
                    self.authorizers[authorizer_id] = ExternalLambdaAuthorizerIntegration(auth, self.opts)
                else:
                    self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.opts, self.service('lambda'), env=self.env)

            elif isinstance(auth, TomcruApiOIDCAuthorizerEP):
                self.authorizers[authorizer_id] = OIDCAuthorizerIntegration(auth, self.opts, env=self.env)

            if authorizer_id not in self.authorizers:
                # raise unless authorizer integ were already defined earlier
                # todo: implement IAM and jwt
                raise NotImplementedError(f'{authorizer_id} - type: {type(auth)}')

        return self.authorizers

    def _build_integrations(self, api, apiopts) -> TomcruEndpoint | None:
        #swagger_converter = self.service('')

        # build controllers
        _index = None
        _swagger: dict[str, TomcruSwaggerIntegrationEP | None] = {"json": None, "html": None, "yaml": None}
        api_root = apiopts.get('api_root', '')
        logger.debug(f"[apigw] {api.api_name} Building integrations for {len(api.routes)} routes")

        # write endpoints to lambda + integrations
        ro: TomcruRouteEP
        for route, ro in api.routes.items():

            endpoint: TomcruEndpoint
            for endpoint in ro.endpoints:
                auth = self.authorizers[endpoint.auth] if endpoint.auth else None

                # refer to integration (proxy controller refers to self.on_request)
                _integration: Callable = self._build_integration_to_endpoint(api, endpoint, auth)

                if _integration is None:
                    logger.warning(f"[apigw] Not found integration for {endpoint}")
                    continue
                self.integrations[endpoint] = _integration
                self._build_method(api, ro, endpoint, apiopts, _integration)

                if endpoint.route == '/':
                    _index = endpoint

        # create swagger UI (both ui and json endpoints are needed)
        # if api.swagger_enabled and api.swagger_ui and _swagger and all(_swagger.values()):
        #     # todo: integrate with yaml too? can this be decided? does swagger UI allow even?
        #     integrate_swagger_ui_blueprint(self.app, _swagger['json'], _swagger['html'])

        return _index

    def _build_integration_to_endpoint(self, api: TomcruApiEP, endpoint: TomcruEndpoint, auth):
        _integration: Callable

        if isinstance(endpoint, TomcruLambdaIntegrationEP):
            # build lambda integration
            _integration = LambdaIntegration(endpoint, auth, self.service('lambda'), env=self.env)
        elif isinstance(endpoint, TomcruSwaggerIntegrationEP):
            return None
            # todo: add support for swagger EP
            # _swagger[endpoint.req_content] = endpoint
            #
            # if endpoint.req_content != 'html':
            #     _integration = SwaggerIntegration(api, endpoint, swagger_converter, env=self.env)
            # else:
            #     continue
        elif isinstance(endpoint, TomcruMockedIntegrationEP):
            if endpoint.file:
                filepath = os.path.join(self.env.spec_path, endpoint.file)

                with open(filepath) as fh:
                    response = json.load(fh)
            else:
                # resolve by swagger examples
                raise NotImplementedError("OpenApi: Examples mock")

            _integration = MockedIntegration(endpoint, auth, response, env=self.env)
        elif isinstance(endpoint, TomcruAwsExposedApiIntegration):
            _integration = self.aws_integ
        else:
            raise NotImplementedError(type(endpoint))

        return _integration

    def _build_method(self, api: TomcruApiEP, route: TomcruRouteEP, endpoint: TomcruEndpoint, apiopts: dict, _integration: object):
        # replace AWS APIGW route scheme to flask routing schema
        api_root = apiopts.get('api_root', '')

        flask_route_key = endpoint.route
        flask_route_key = self.rgx_greedy_path_a2f.sub(r'<path:\1>', flask_route_key)
        flask_route_key = flask_route_key.replace('{', '<').replace('}', '>')

        _api_route = f'{endpoint.method.upper()} {api_root}{flask_route_key}'

        add_endpoint(self.parent.apps[api.api_name], _api_route, endpoint.endpoint_id, self._on_request)

    def _build_acl(self, api: TomcruApiEP, acl: dict):
        if acl is None:
            return

        app: Flask = self.parent.apps[api.api_name]

        f = cors(acl)
        app.after_request(lambda resp: f(request, resp))

    def _build_extra_route_handlers(self, api: TomcruApiEP, index: TomcruEndpoint | None = None):
        pass

    def _on_request(self, **kwargs):
        port = int(request.server[1])

        # find route by flask request route
        aws_route_key = str(request.url_rule)
        aws_route_key = self.rgx_greedy_path_f2a.sub(r'{\1+}', aws_route_key)
        aws_route_key = aws_route_key.replace('<', '{').replace('>', '}')

        ep, api = self.get_called_endpoint(
            port=port,
            route_key=aws_route_key,
            vendor_endpoint=request.endpoint,
            **kwargs
        )

        if not ep or not api:
            return dict(
                statusCode=404,
                body=""
            )

        integ = self.integrations[ep]
        logger.debug(f'[apigw] Calling integration for {ep.endpoint_id}: {integ}')

        base_headers = {
            **self.opts.get('default.headers', {}),
            **self.opts.get(f'apis.{api.api_name}.headers', {})
        }
        response = integ(base_headers=base_headers, **kwargs)

        if api.swagger_check_models and api.spec_resolved_schemas:
            # todo: make swagger model checker work
            pass
            # try:
            #     self.service()
            #     self.p.serv("aws:onpremise:model_checker").check_response(api, ep, response, env=self.env)
            # except Exception as e:
            #     if self.env == 'dev' or self.env == 'debug':
            #         raise e
            #     else:
            #         print("!! Swagger model checker raised an exception: ", str(e))

        if isinstance(response, tuple) and response[0] == '__FILE__':
            return self.handle_file(response[1])
        return response

    def handle_file(self, filepath):
        # todo: handle streams later?
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        return send_from_directory(directory=directory, path=filename)

    def aws_integ(self, serv_id, proxy_args=None, **kwargs):
        """
        special, dedicated HTTP integration for AWS service endpoints.
        You can use this to expose your Tomcru HTTP app with AWS services,
        so that AWS sdk can rely on it

        :param serv_id: AWS service identifier
        :param proxy_args:
        :param kwargs:
        :return:
        """

        # calls aws service
        srv = self.service(serv_id)
        if not srv:
            return "", 404

        secret_getter = self.service('iam').get_secret_from_key
        return aws_integ.on_request(srv, request, secret_getter)

    def print_endpoints(self, app, apiopts):
        flask_jerry_setup(app, apiopts)
        print_endpoints(app)
