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

    def parse_environments(self):
        env_path = os.path.join(self.cfg.app_path, 'envspec')

        for root, dirs, files, in os.walk(env_path):
            for base in filter(lambda f: f == 'tomcru.toml', files):
                envcfg = self.load_env(os.path.join(env_path, root))
                envcfg.app_path = self.cfg.app_path

                self.proj.envs[envcfg.env_id] = envcfg

    def load_env(self, basepath) -> TomcruEnvCfg:
        id = os.path.basename(basepath)

        cfg = toml.load(os.path.join(basepath, 'tomcru.toml'))
        envcfg = TomcruEnvCfg(id, cfg)

        for root, dirs, files in os.walk(basepath):
            root_dirname = os.path.basename(root)

            if 'envvars' == root_dirname:
                # load envvars
                for file in files:
                    envvars_wrap = toml.load(os.path.join(root, file))

                    if 'lambdas' in envvars_wrap:
                        envvar_groups = unflatten_1lv(flatten(envvars_wrap['lambdas'], separator='/'))

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

        return envcfg

    # def parse_envvars(self, vendor):
    #     """
    #     Parses lambda and other envvars configured
    #     :return:
    #     """
    #
    #     path = f'{self.cfg.app_path}/cfg/{vendor}'
    #
    #     for env in os.listdir(path):
    #         envvar_path = os.path.join(path, env, 'envvars')
    #
    #         if os.path.exists(envvar_path):
    #             for root, dirs, files in os.walk(envvar_path):
    #                 for file in files:
    #                     if file.endswith('.ini'):
    #                         # envvar file
    #                         self.add_envvars(os.path.join(envvar_path, file), env, vendor)

    # def _get_param(self, integ_opts, param, default_val) -> str:
    #     r = next(filter(lambda x: x.startswith(param+':'), integ_opts), "").removeprefix(param+':')
    #
    #     if not r:
    #         # see if api config contains
    #         r = default_val
    #
    #     return r

    def add_envvars(self, file_path, env, vendor):
        raise NotImplementedError()
    #     """
    #     Adds enviornment variables ini file defined for:
    #     - lambda
    #
    #     :param file_path: ini filepath
    #     :param env: environment to configure envvars for
    #     :param vendor: cloud vendor (aws | azure | gpc)
    #     :return:
    #     """
    #     if not os.path.isabs(file_path):
    #         file_path = os.path.join(self.cfg.app_path, 'cfg', vendor, env, 'envvars', file_path)
    #
    #     if not os.path.exists(file_path):
    #         raise Exception(f"Define your envvars in the following directory structure: project/cfg/{vendor}/<env>/envvars/<filename>.ini")
    #
    #     self.cfg.envs[env].update(
    #         dict(load_settings(file_path).conf)
    #     )
