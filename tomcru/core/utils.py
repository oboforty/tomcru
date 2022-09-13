import sys
from importlib import import_module


def load_serv(path, name):
    sys.path.append(path)
    m = import_module(name)
    sys.path.remove(path)
    return m
