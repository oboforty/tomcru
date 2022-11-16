import sys
import os.path

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location
from importlib import import_module


class MyMetaFinder(MetaPathFinder):

    def __init__(self, keywords, paths, injected_obj=None):
        if not isinstance(keywords, (set, type(None))):
            keywords: set = {keywords}
        if not isinstance(paths, list):
            paths = [paths]

        self.keywords: set = keywords
        self.paths: list = paths
        self.injected_obj = injected_obj

        if self.injected_obj and isinstance(self.paths, list) and len(self.paths) > 1:
            raise NotImplementedError("If you provide an injectable object, please provide a single path")

    def find_spec(self, fullname, path, target=None):
        if self.keywords:
            for keyword in self.keywords:
                if fullname == keyword or keyword in fullname:
                    break
            else:
                return None

        for entry in self.paths:
            # if path is None or path == "":
            #     path = [os.getcwd()] # top level import --
            if "." in fullname:
                *parents, name = fullname.split(".")
            else:
                name = fullname

            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                # shouldn't happen
                return None

            _loader = MyLoader(filename, self.injected_obj) if self.injected_obj else None
            return spec_from_file_location(fullname, filename, loader=_loader, submodule_search_locations=submodule_locations)

    def __repr__(self):
        return f'<{self.__class__.__name__} {", ".join(self.keywords)} paths={", ".join(self.paths)} object={self.injected_obj}>'

class MyLoader(Loader):
    def __init__(self, filename, injectable):
        self.filename = filename
        self.injectable = injectable

    def create_module(self, spec):
        return self.injectable

    def exec_module(self, module):
        return
        # with open(self.filename) as f:
        #     data = f.read()
        #
        # # manipulate data some way...
        #
        # exec(data, vars(module))

    def __repr__(self):
        return f'<{self.__class__.__name__} {", ".join(self.filename)} object={self.injectable}>'

_registered_finders = []


def inject(service_filter_keywords, service_paths, injectable=None):
    """
    Injects requested module

    :param service_filter_keywords: list or str of keyword(s) that serve as filter logic to import modules.
        If None is provided, then all packages are loaded with the internal loader
    :param service_paths: list or str of path to module that replaces dependency
    :param injectable: if provided, this object will be imported instead of built-in path-based Loader
    """
    global _registered_finders

    sys.meta_path.insert(0, f := MyMetaFinder(service_filter_keywords, service_paths, injectable))
    _registered_finders.append(f)

    return f


def clean_inject(f):
    finder = next(filter(lambda x: f in x.keywords, _registered_finders))

    sys.meta_path.remove(finder)
    _registered_finders.remove(finder)


def cleanup_injects():
    """
    Removes injected modules from sys path.
    Please note that python's import cache will still serve the injected modules regardless!
    """
    for f in _registered_finders:
        sys.meta_path.remove(f)

    _registered_finders.clear()
