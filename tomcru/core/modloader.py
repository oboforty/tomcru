import sys
from importlib import import_module
import imp


def load_serv(path, name):
    # try:
    #     f, filename, description = imp.find_module(name, [path])
    #     return imp.load_module(name, f, filename, description)
    # except ImportError as e:
    #     raise e

    try:
        sys.path.append(path)
        m = import_module(name)
        sys.path.remove(path)
    except Exception as e:
        if hasattr(e, 'name') and e.name == name:
            return None
        raise e

    return m
