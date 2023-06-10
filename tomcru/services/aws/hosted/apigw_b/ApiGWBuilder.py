import logging
import os.path
from collections import defaultdict


from tomcru.services.ServiceBase import ServiceBase
from .ApiGWSubserviceBase import ApiGWSubserviceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))

from tomcru.services.aws.hosted.apigw_b.flask_b import ApiGWFlaskSubservice
from tomcru.services.aws.hosted.apigw_b.ws_b import ApiGWWebsocketsSubservice

logger = logging.getLogger('tomcru')


class ApiGWBuilder(ServiceBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sub_builders: dict[str, ApiGWSubserviceBase] = {}
        self.apps: dict[str, object] = {}
        self.port2apps: dict[int, set] = defaultdict(set)

        self.autobuild = self.opts.get('service.autobuild', None)

        if self.opts.get('service.target_http') == 'flask':
            self.sub_builders['http'] = ApiGWFlaskSubservice(self, *args, **kwargs)

        if self.opts.get('service.target_ws') == 'websockets':
            self.sub_builders['ws'] = ApiGWWebsocketsSubservice(self, *args, **kwargs)

    def get_app(self, api_name):
        if api_name not in self.apps:

            raise Exception(f"Api {api_name} not found! Available apis: {', '.join(self.apps.keys())}")
        return self.apps[api_name], self.opts.get(f'apis.{api_name}', {})

    def inject_dependencies(self):
        # inject deps is called before init, first create all app objects
        # so that apps with attach_to can be injected into already existing ones in init
        if self.autobuild:
            for api_name in self.autobuild:
                self.build_api(api_name, attached_apps=False)

    def init(self):
        if self.autobuild:
            for api_name in self.autobuild:
                self.build_api(api_name, attached_apps=True)

    def build_api(self, api_name, attached_apps=False):
        """
        Build API

        :param api_name:
        :param attached_apps:
        """
        logger.info(f"[apigw] Building api {api_name} (attach={attached_apps})")

        # todo: check if app has been built

        api = self.p.cfg.apis[api_name]
        apiopts = {**self.opts.get('default', {}), **self.opts.get(f'apis.{api_name}', {})}

        if 'attach_to' in apiopts:
            if not attached_apps:
                return None

            # attach this api to an already existing app
            serv_id = apiopts['attach_to']['service']
            parent_api_name = apiopts['attach_to']['app']

            try:
                parent_app, parent_opts = self.service(serv_id).get_app(parent_api_name)
            except:
                raise Exception(
                    f"Referenced app not found in attach_to: {serv_id}->{parent_api_name}")

            logger.debug(f"[apigw] {api_name} attaching to {parent_api_name} ({serv_id})")
            app = self.apps[api.api_name] = parent_app
        else:
            app = self.apps[api.api_name] = self.sub_builders[api.api_type].create_app(api, apiopts)

        conn_id = api.api_name
        self.service('apigw_manager').add_app(self, conn_id)

        self.sub_builders[api.api_type].build_api(api, apiopts)
        self.port2apps[apiopts['port']].add(api.api_name)

        return app, apiopts

    def print_endpoints(self, app, apiopts):
        return self.sub_builders[app.api_type].print_endpoints(app, apiopts)
