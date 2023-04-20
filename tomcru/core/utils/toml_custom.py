import configparser

import toml

from tomcru_jerry.utils import get_dict_hierarchy


class SettingWrapper:
    def __init__(self, conf):
        self.conf = conf

    def __getitem__(self, item):
        return self.conf.get(item)

    def __len__(self):
        return len(self.conf)

    def get(self, opts, default=None, cast=None):
        return get_dict_hierarchy(self.conf, opts, default, cast)

    @property
    def view(self):
        return self.conf.copy()

    def __repr__(self):
        return f'<SettingWrapper {repr(self.conf)}>'


def load_settings(file, **kwargs) -> SettingWrapper:
    config = configparser.ConfigParser(**kwargs)
    config.optionxform = str
    config.read(file)

    conf = config._sections

    if conf is None:
        return None

    for okey, oval in conf.items():
        for key, val in oval.items():
            if val.lower() in ('yes', 'true'):
                conf[okey][key] = True
            elif val.lower() in ('no', 'false'):
                conf[okey][key] = False
            elif ',' in val:
                conf[okey][key] = val.split(',')

    return SettingWrapper(conf)
