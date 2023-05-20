import os

from .logger import init_logging
from .obj_store import ObjStore
from .servmgr import ServiceManager
from ..appbuilders.envmapping import map_env_to_appbuilder
from ..cfgparsers import BaseCfgParser, _parsers
from .cfg.proj import TomcruSubProjectCfg, TomcruEnvCfg
from ..appbuilders.faas.InjectableAppBase import InjectableAppBase


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
        self.envcfgs: dict[str, TomcruEnvCfg] = {}
        self.envs: dict[str, InjectableAppBase] = {}

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

        for name, cls in _parsers.items():
            cfgparser.add_parser(name, cls(cfgparser, name))

        self.cfgs[cfgparser.name] = cfgparser.cfg
        self.active_cfg = cfgparser.name

        return cfgparser

    def env(self, env_id, cfg_id=None, **kwargs) -> 'InjectableAppBase':
        """

        :param env_id:
        :param kwargs:
        :return:
        """
        _env = self.envs.get(env_id)

        if not _env:
            _cfg = self.cfg if cfg_id is None else self.cfgs[cfg_id]

            envcfg = self.envcfgs[env_id]
            init_logging(envcfg.logging.get('loglvl', 'DEBUG'), envcfg.logging.get('filepath'))

            _env = map_env_to_appbuilder(self, _cfg, envcfg)
            self.envs[env_id] = _env

        return _env
