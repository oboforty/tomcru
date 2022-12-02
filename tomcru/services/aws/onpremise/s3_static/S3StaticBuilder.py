import sys
import os
import shutil
import subprocess
import json

import eme.static, eme.entities
from tomcru import TomcruApiDescriptor, TomcruProject


class S3StaticBuilder:

    def __init__(self, project: TomcruProject, static_cfg):
        self.cfg = project.cfg
        self.opts = static_cfg
        self.p = project

        self.env: str = None
        self.resp = None

    def build_app(self, env: str):
        self.env = env
        directory = self.opts.get('app.path', 'static')

        script_path = os.path.join(self.cfg.app_path, directory)
        em = eme.static.EmeStaticWebsite("index.html", script_path)

        em.build(envcfg=self.cfg)

        em.host = self.opts.get('app.host', '0.0.0.0')
        em.port = self.opts.get('app.port', 5000)

        return em

