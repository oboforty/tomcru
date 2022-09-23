import sys
import os.path

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location
from importlib import import_module


class MyMetaFinder(MetaPathFinder):

    def __init__(self, keywords, paths, cls=None):
        if not isinstance(keywords, set):
            keywords = set([keywords])
        if not isinstance(paths, list):
            paths = [paths]

        self.keywords = keywords
        self.paths = paths
        self._cls = cls

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

            _loader = self._cls(filename) if self._cls else None
            return spec_from_file_location(fullname, filename, loader=_loader, submodule_search_locations=submodule_locations)

_registered_finders = []


def inject(service_filter_keywords, service_paths):
    """
    Injects requested module

    :param service_filter_keywords: list or str of keyword(s) that serve as filter logic to import modules
    :param service_paths: list or str of path to module that replaces dependency
    """
    global _registered_finders

    sys.meta_path.insert(0, f := MyMetaFinder(service_filter_keywords, service_paths))
    _registered_finders.append(f)


def cleanup_injects():
    """
    Removes injected modules from sys path.
    Please note that python's import cache will still serve the injected modules regardless!
    """
    for f in _registered_finders:
        sys.meta_path.remove(f)

    _registered_finders.clear()
