import os
from flatten_json import flatten
from collections import defaultdict

from tomcru.core.cfg.proj import TomcruEnvCfg
from tomcru.core.utils.toml_custom import toml, load_settings, SettingWrapper

def unflatten_1lv(d):
    u = defaultdict(dict)

    for k,v in d.items():
        s = k.split('/')[-1]
        u[k.removesuffix('/'+s)][s] = v

    return dict(u)


class EnvParser:
    def __init__(self, cfgparser, name):
        self.cfg = cfgparser.cfg
        self.proj = cfgparser.proj
        self.cfgparser = cfgparser
        self.cfg_name = name

    def parse_environments(self, env_envvar=None):
        env_path = os.path.join(self.cfg.app_path, 'envspec')

        for root, dirs, files, in os.walk(env_path):
            for base in filter(lambda f: f == 'tomcru.toml', files):
                envcfg = self.load_env(os.path.join(env_path, root), env_envvar=env_envvar)
                envcfg.app_path = self.cfg.app_path

                self.proj.envcfgs[envcfg.env_id] = envcfg

    def load_env(self, basepath, env_envvar=None) -> TomcruEnvCfg:
        id = os.path.basename(basepath)

        cfg = toml.load(os.path.join(basepath, 'tomcru.toml'))
        envcfg = TomcruEnvCfg(id, cfg)
        envcfg.global_envvars = {}

        for root, dirs, files in os.walk(basepath):
            root_dirname = os.path.basename(root)

            if 'envvars' == root_dirname:
                # load envvars
                for file in files:
                    envvars_wrap = toml.load(os.path.join(root, file))

                    if 'lambdas' in envvars_wrap:
                        envvar_groups = unflatten_1lv(flatten(envvars_wrap['lambdas'], separator='/'))

                        envcfg.global_envvars.update(envvar_groups.pop('__ALL__', {}))

                        for lambda_id, envvars in envvar_groups.items():
                            envcfg.envvars_lamb[lambda_id].update(envvars)
            else:
                # other configs are loaded as service specifiers
                for file in filter(lambda f: f.endswith('.toml'), files):
                    if file == 'tomcru.toml':
                        continue
                    opts_wrap = toml.load(os.path.join(root, file))

                    if opts_wrap:
                        for serv, opts in opts_wrap.items():
                            envcfg.serv_opts[serv] = SettingWrapper(opts)
                    else:
                        # add empty files as well
                        serv, ext = os.path.splitext(file)
                        if ext == '.toml':
                            envcfg.serv_opts[serv] = SettingWrapper({})

        # update envvars with global envvars
        if env_envvar:
            envcfg.global_envvars[env_envvar] = envcfg.env_id

        return envcfg

    def add_envvars(self, file_path, env, vendor):
        raise NotImplementedError()

    def add_global_envvars(self, env_id, envvars: dict):
        envcfg = self.proj.envcfgs[env_id]

        for lambda_id, d in envcfg.envvars_lamb.items():
            d.update(envvars)
