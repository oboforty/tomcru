import logging
import os.path


from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class ApiGWBuilder(ServiceBase):
    INIT_PRIORITY = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_app(self, api_name):
        if api_name not in self.apps:
            raise Exception(f"Api {api_name} not found! Available apis: {', '.join(self.apps.keys())}")
        return self.apps[api_name], self.opts.get(f'apis.{api_name}', {})

    def inject_dependencies(self):
        pass

    def init(self):
        pass
