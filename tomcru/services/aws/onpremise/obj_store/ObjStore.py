import inspect
import os
import sys
import traceback
from importlib import import_module

from tomcru import TomcruProject
from tomcru import utils


class ObjStore:
    def __init__(self, project: TomcruProject, opts: dict):
        """
        Stores AWS service objects to be accessible both internally in a tomcru app and externally (e.g. tomcru used as a library)
        :param project:
        :param opts:
        """
        self.cfg = project.cfg
        self.opts = opts
        self.objects = {}

    def get(self, serv, obj_id):
        return self.objects.get(serv+':'+obj_id)

    def add(self, serv, obj_id, obj):
        self.objects[serv+':'+obj_id] = obj

    def has(self, serv, obj_id):
        return serv+':'+obj_id in self.objects
