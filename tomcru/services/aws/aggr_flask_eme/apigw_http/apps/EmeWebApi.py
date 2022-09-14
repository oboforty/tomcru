from eme.website import WebsiteAppBase, RegexConverter
from flask import Flask

from tomcru import TomcruCfg


class EmeWebApi(Flask, WebsiteAppBase):

    def __init__(self, tomcrucfg: TomcruCfg, cfg: dict):
        Flask.__init__(self, '')
        self.url_map.converters['regex'] = RegexConverter
        WebsiteAppBase.__init__(self, {
            'website': {
                'type': 'samapi'
            }
        })

        self.boto3 = None

    def start(self):
        self.run(self.host, self.port, threaded=True, debug=self.debug)
