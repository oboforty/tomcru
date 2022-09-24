from eme.website import WebsiteAppBase, RegexConverter
from flask import Flask


from tomcru import TomcruApiDescriptor


class EmeWebApi(Flask, WebsiteAppBase):

    def __init__(self, tomcrucfg: TomcruApiDescriptor, cfg: dict):
        Flask.__init__(self, '')
        self.url_map.converters['regex'] = RegexConverter
        WebsiteAppBase.__init__(self, {
            'website': {
                'type': 'samapi'
            }
        })

        self.host = cfg.get('host')
        self.port = int(cfg.get('port', 5000))
        self.api_name = f'{tomcrucfg.api_name}:{self.port}'
        self.is_main_thread = cfg.get('main_api', False)

        self.boto3 = None

    def start(self):
        self.run(self.host, self.port, threaded=True, debug=self.debug)
