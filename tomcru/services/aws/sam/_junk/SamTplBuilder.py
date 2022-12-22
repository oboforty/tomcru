import os
import re
from collections import defaultdict

from awssam.AwsSamCfg import AwsSamCfg, AwsSamRouteDescriptor, AwsSamEndpointDescriptor
from eme.entities import load_settings
from zipfile import ZipFile


def raw_str(s):
    return ''.join(map(lambda x: x.title(), s.replace(':', '_').replace('/', '_').replace('$', '').split('_')))

class SamTplBuilder:

    def __init__(self, cfg: AwsSamCfg):
        self.cfg = cfg

    def build_template(self, env, name):
        if os.path.exists(self.cfg.app_path + '/sam/core.yaml'):
            with open(self.cfg.app_path + '/sam/core.yaml') as fh:
                self.tpl_core = fh.read()
        else:
            with open(self.cfg.tpl_path + '/core.yaml') as fh:
                self.tpl_core = fh.read()

        with open(self.cfg.tpl_path + '/apigw/httpapi.yaml') as fh:
            self.tpl_http = fh.read()
        with open(self.cfg.tpl_path + '/apigw/wsapi.yaml') as fh:
            self.tpl_ws = fh.read()
        with open(self.cfg.tpl_path + '/lambda/lambda.yaml') as fh:
            self.tpl_lambda = fh.read()
        with open(self.cfg.tpl_path + '/lambda/layer.yaml') as fh:
            self.tpl_layer = fh.read()

        envs = load_settings(self.cfg.app_path+'/sam/cfg/'+env+'/envlist.ini')

        self.tpl_integ = None
        self.tpl_integ_ws = None
        # for file in os.listdir(self.cfg.app_path + '/sam/integrations'):
        #     with open(f'{self.cfg.app_path}/sam/integrations/{file}') as fh:
        #         self.tpl_integ[os.path.splitext(file)[0]] = fh.read()
        with open(f'{self.cfg.tpl_path}/apigw/integ_normal.yaml') as fh:
            self.tpl_integ = fh.read()
        with open(f'{self.cfg.tpl_path}/apigw/integ_ws.yaml') as fh:
            self.tpl_integ_ws = fh.read()
        tpl_parts = []

        if os.path.exists(self.cfg.app_path + '/sam/tpl'):
            for file in os.listdir(self.cfg.app_path + '/sam/tpl'):
                with open(f'{self.cfg.app_path}/sam/tpl/{file}') as fh:
                    tpl_parts.append(fh.read())

        with open(name, 'w') as fh:
            # SAM core:
            fh.write(self.tpl_core)

            for tpl_part in tpl_parts:
                fh.write(tpl_part)

            for (layer,_,_,_,_) in self.cfg.layers:
                self._parse_layer(layer, fh)

            self.build_lambdas(fh, envs)

            self.build_apis(fh)

            self.build_websocket(fh)

    def build_lambdas(self, fh, envs):
        default_role = 'LambdaExecRole'

        # write lambdas:
        for group, lamb, layers in self.cfg.lambdas:
            lvars = envs.get(lamb)

            fh.write(self.tpl_lambda.format(name=lamb, group=group, role=default_role))

            if layers:
                fh.write(f"      Layers:\n")

                for layer in layers:
                    if layer == 'YannyDalLayer':
                        fh.write(f"        - !Ref {layer}Arn\n")
                    else:
                        fh.write(f"        - !Ref {layer}\n")
            if lvars:
                fh.write(f"      Environment:\n")
                fh.write(f"         Variables:\n")

                for k,v in lvars.items():
                    fh.write(f"             {k}: {v}\n")

            fh.write('\n')

    def build_apis(self, fh):
        for api_name, routes in self.cfg.apis.items():
            ro: AwsSamRouteDescriptor

            # write api base
            fh.write(self.tpl_http.format(name=api_name))

            # write endpoints to lambda + integrations
            for route, ro in routes.items():
                fh.write(f'          {route}:\n')

                endpoint: AwsSamEndpointDescriptor
                for endpoint in ro.endpoints:
                    _q_params = ""
                    # add request parameter mapping
                    r = re.search(r"\{([a-zA-Z0-9_]*)\+?\}", ro.route)

                    if r:
                        _q_params = "requestParameters:"
                        rgroups = r.groups()

                        for group in rgroups:
                            _q_params += f'\n                  "overwrite:querystring.{group}": "$request.path.{group}"'

                    fh.write(f'            {endpoint.method.lower()}:\n')
                    fh.write(self.tpl_integ.format(
                        lamb=endpoint.lamb,
                        params=_q_params
                    ))

                fh.write('\n')
            fh.write('\n')


    def build_websocket(self, fh):
        has_authorizer = False

        for api_name, routes in self.cfg.wss.items():
            ro: AwsSamRouteDescriptor
            endpoint: AwsSamEndpointDescriptor

            # write api base
            fh.write(self.tpl_ws.format(
                name=api_name,
                api_routenames="@todo: later"
            ))

            # write endpoints to lambda + integrations
            for route, ro in routes.items():
                endpoint: AwsSamEndpointDescriptor
                for endpoint in ro.endpoints:
                    is_wsconn_and_authorizer = endpoint.route == '$connect' and True

                    if is_wsconn_and_authorizer:
                        authorizer = f'AuthorizationType: CUSTOM\n      AuthorizerId: !Ref WsAuthorizer{ro.api_name}'
                    else:
                        authorizer = 'AuthorizationType: NONE'

                    fh.write(self.tpl_integ_ws.format(
                        route=endpoint.route.replace(':', '_'),
                        route_raw=raw_str(endpoint.route),
                        endpoint_id=endpoint.endpoint_id,
                        endpoint_raw=raw_str(endpoint.endpoint_id),
                        authorization=authorizer,
                        lamb=endpoint.lamb,
                        api_name=ro.api_name
                    ))
            fh.write('\n')

    def _parse_layer(self, name, fh):
        fh.write(self.tpl_layer.format(name=name, file=name))

    def build_layers(self):
        for (layer_name, packages, folder, in_house) in self.cfg.layers:
            if not in_house:
                continue
            if folder is None:
                folder = layer_name#[0:-5]

            pck_dir = 'layers/'
            pckvdir = 'python/lib/python3.10/site-packages/'

            basepath = f'{self.cfg.app_path}layers/{folder}'

            with ZipFile(f'{basepath}{layer_name}.zip', 'w') as zipObj2:
                for pck in os.listdir(os.path.join(basepath,packages)):
                    path = os.path.join(basepath,packages,pck)

                    if os.path.isfile(path):

                    else:
                        # parse files in package
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                rel_dir = os.path.relpath(root, path)
                                rel_file = os.path.join(rel_dir, file)
                                abs_file = os.path.join(root, file)

                                if '__pycache__' in abs_file or '.log' in abs_file:
                                    continue
                                zippath = os.path.join(pckvdir, pck, rel_dir, file)
                                zipObj2.write(abs_file, zippath)
