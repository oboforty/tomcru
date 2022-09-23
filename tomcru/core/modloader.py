import sys
from importlib import import_module
import imp

def load_serv(path, name):
    # try:
    #     f, filename, description = imp.find_module(name, [path])
    #     return imp.load_module(name, f, filename, description)
    # except ImportError as e:
    #     raise e

    sys.path.append(path)
    m = import_module(name)
    sys.path.remove(path)

    return m
