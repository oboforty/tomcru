from .cfg import TomcruCfg, TomcruEndpointDescriptor, TomcruRouteDescriptor

from ..cfgparsers.BaseCfgParser import BaseCfgParser

class TomCruProject:

    def __init__(self, app_path):
        self.app_path = app_path
        self.cfgparser = None
        self.cfgs = {}

    def __enter__(self) -> BaseCfgParser:
        return self.cfgparser

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cfgparser.cfg:
            self.cfgs[self.cfgparser.name] = self.cfgparser.cfg

    def project_builder(self, name):
        self.cfgparser = BaseCfgParser(self, name)
        self.cfgparser.create_cfg(self.app_path)

        return self
