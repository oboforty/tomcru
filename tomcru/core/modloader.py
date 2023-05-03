import sys
from importlib import import_module
import imp


def load_serv(path, name, debug=False):
    # try:
    #     f, filename, description = imp.find_module(name, [path])
    #     return imp.load_module(name, f, filename, description)
    # except ImportError as e:
    #     raise e

    try:
        _ctx_orig = dict(sys.modules)

        sys.path.append(path)
        m = import_module(name)
        sys.path.remove(path)

        sys.modules.clear()
        sys.modules.update(_ctx_orig)

    except Exception as e:
        raise e
        # if not debug and hasattr(e, 'msg') and e.msg.startswith("No module named"):
        #     return None

    return m
