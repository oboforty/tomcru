import sys
from importlib import import_module


def load_tomcru_mod(path, name):
    sys.path.append(path)
    m = import_module(name)
    sys.path.remove(path)
    return m


class TomcruCore:
    def __init__(self):
        self.appbuilders = {}
        self.cfgparsers = {}
        self.cloudvendors = {}
        self.authorizer_registers = {}
    #
    # def load_tomcru_appbuilder(self, path, name):
    #     b = load_tomcru_mod(path, name)
    #     self.appbuilders[name] = b.build_app
    #
    # def load_tomcru_appbuilder(self, path, name):
    #     b = load_tomcru_mod(path, name)
    #     self.appbuilders[name] = b.build_app
