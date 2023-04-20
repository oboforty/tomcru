import os
from deprecated import deprecated

from .obj_store import ObjStore
from .servmgr import ServiceManager
from ..appbuilders.envmapping import map_env_to_appbuilder
from ..cfgparsers.EnvParser import EnvParser
from ..cfgparsers.SwaggerCfgParser import SwaggerCfgParser
from ..cfgparsers.BaseCfgParser import BaseCfgParser
from ..cfgparsers.MergeCfgParser import MergeCfgParser
from .cfg.proj import TomcruSubProjectCfg, TomcruEnvCfg


class TomcruProject:

    def __init__(self):
        self.pck_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        # list of app configs that can be merged
        # cfgparser: BaseCfgParser | None = None
        self.cfgs: dict[str, TomcruSubProjectCfg] = {}
        self.active_cfg = None

        # list of cloud services
        # self.services = {}

        # list of environment apps
        self.envs: dict[str, TomcruEnvCfg] = {}

        self.debug_builders = False
        self.objmgr = ObjStore(self, use_cache=False)
        self.srvmgr = ServiceManager(self, self.objmgr)

        self.debug = True

    @property
    def cfg(self) -> TomcruSubProjectCfg:
        return self.cfgs[self.active_cfg]

    def project_builder(self, name, app_path=None):
        # default cfg parser
        cfgparser = BaseCfgParser(self, name)
        cfgparser.create_cfg(app_path, self.pck_path)

        cfgparser.add_parser("swagger", SwaggerCfgParser(cfgparser, name))
        cfgparser.add_parser("merge", MergeCfgParser(cfgparser, name))
        cfgparser.add_parser("env", EnvParser(cfgparser, name))

        self.cfgs[cfgparser.name] = cfgparser.cfg
        self.active_cfg = cfgparser.name

        return cfgparser

    def env(self, env_id, cfg_id=None, **kwargs) -> 'InjectableAppBase':
        """

        :param env_id:
        :param kwargs:
        :return:
        """
        _cfg = self.cfg if cfg_id is None else self.cfgs[cfg_id]

        # todo: itt: return EnvAppBuilder
        return map_env_to_appbuilder(self, _cfg, self.envs[env_id])

    @deprecated("Don't call services from the project, instead use environment")
    def serv(self, name):
        env = self.find_env_from_legacy_name(name)

        # load service into cache; cfg
        return self.env(env.env_id).serv(name)

    @deprecated("Don't call services from the project, instead use environment")
    def find_env_from_legacy_name(self, name) -> TomcruEnvCfg:
        n = name.split(':')
        vendor, target, service_id = n
        if not target:
            target = ''
        if not vendor:
            vendor = 'general'

        if target == 'onpremise':
            # @note: hosted frameworks were incorrectly labeled as onpremise
            target = 'hosted'

        env: TomcruEnvCfg = next(filter(lambda env: env.target == target and vendor in env.vendors, self.envs.values()), None)

        if env is None:
            raise Exception(f"Service not found: {name}")

        return env
