import os.path
from collections import defaultdict

from .api import TomcruApiAuthorizerDescriptor, TomcruApiDescriptor
from ..utils.toml_custom import SettingWrapper


class TomcruProjectCfg:
    def __init__(self):
        self.apis: dict[str, TomcruApiDescriptor] = {}
        self.authorizers: dict[str, TomcruApiAuthorizerDescriptor] = {}

        self.layers = []
        self.services: dict[str, SettingWrapper] = {}

    def update(self, cfg: 'TomcruProjectCfg'):
        self.authorizers.update(cfg.authorizers)

        self.layers.extend(cfg.layers)

        # additive merge, not override
        api: TomcruApiDescriptor
        for api_name, api in cfg.apis.items():
            if api_name in self.apis:
                self.apis[api_name].update(api)
            else:
                self.apis[api_name] = api

        for serv_id, serv_cfg in cfg.services.items():
            if serv_id in self.services:
                self.services[serv_id].conf.update(serv_cfg.conf)
            else:
                self.services[serv_id] = serv_cfg


class TomcruSubProjectCfg(TomcruProjectCfg):

    def __init__(self, path: str, pck_path: str):
        """

        :param path:
        :param pck_path:
        """
        super().__init__()

        self.app_path = path + '/'
        self.pck_path = pck_path + '/'


class TomcruEnvCfg:
    def __init__(self, env_id: str, cfg: dict):
        self.app_path: str | None = None
        self.env_id: str = env_id
        self.env: str = cfg['envcfg']['env']
        self.vendors: list[str] = cfg['envcfg']['vendors']
        self.target: str = cfg['envcfg']['target']
        self.service_type: str = cfg['envcfg'].get('service_type', 'faas')

        # environment variables for various services
        self.global_envvars: dict[str, str] = {}
        self.envvars_lamb: dict[str, dict[str, dict]] = defaultdict(dict)

        # service specifications
        self.serv_opts: dict[str, SettingWrapper] = {}

    @property
    def spec_path(self) -> str:
        return os.path.join(self.app_path, 'envspec', self.env)
