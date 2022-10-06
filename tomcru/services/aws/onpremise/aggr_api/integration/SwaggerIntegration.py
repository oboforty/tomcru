import json
import os
from io import StringIO

#import yaml
from tomcru.yaml_custom import yaml
from eme.entities import EntityJSONEncoder

from flask import request, Response, Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from tomcru import TomcruApiDescriptor, TomcruSwaggerIntegration

from .TomcruApiGWHttpIntegration import TomcruApiGWHttpIntegration


class SwaggerIntegration(TomcruApiGWHttpIntegration):

    def __init__(self, api: TomcruApiDescriptor, endpoint: TomcruSwaggerIntegration, auth, env=None):
        # self.spec = api.spec
        # self.api_name = api.api_name
        self.endpoint = endpoint
        self.auth_integ = auth
        self.env = env
        self.swagger_content: str | None = None

        if self.endpoint.type == 'ui':
            # display swagger UI
            pass
        elif self.endpoint.type == 'spec':
            self.get_swagger_content(api, endpoint)
        else:
            raise NotImplementedError("issue")

    def on_request(self, **kwargs):

        # todo: we don't really need auth here, but maybe?

        if self.endpoint.type == 'ui':
            # display swagger UI
            return "hello teszomsz"
        elif self.endpoint.type == 'spec':
            r = Response(self.swagger_content, status=200)
            r.headers['content-type'] = self.content_type
            return r

    def get_swagger_content(self, api: TomcruApiDescriptor, endpoint):
        self.content_type = f'application/{endpoint.req_content}'

        if 'json' == endpoint.req_content:
            self.swagger_content = json.dumps(api.spec)
        else:
            sth = StringIO()
            yaml.dump(api.spec, stream=sth)
            self.swagger_content = sth.getvalue()


def integrate_swagger_ui_blueprint(app: Flask, swagger_endpoint: TomcruSwaggerIntegration, ui_endpoint: TomcruSwaggerIntegration):
    swaggerui_blueprint = get_swaggerui_blueprint(
        ui_endpoint.route,
        swagger_endpoint.route,
        config={
            # Swagger UI config overrides
            #'app_name':
        },
        # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
        #    'clientId': "your-client-id",
        #    'clientSecret': "your-client-secret-if-required",
        #    'realm': "your-realms",
        #    'appName': "your-app-name",
        #    'scopeSeparator': " ",
        #    'additionalQueryStringParams': {'test': "hello"}
        # }
    )

    app.register_blueprint(swaggerui_blueprint)
