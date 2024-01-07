import sys
import configparser


if sys.version_info > (3, 10):
    import tomllib

    def toml_load(fn):
        with open(fn, 'rb') as fh:
            return tomllib.load(fh)
else:
    import toml
    load_toml = toml


from tomcru_jerry.utils import get_dict_hierarchy


class SettingWrapper:
    def __init__(self, conf):
        self.conf = conf

    def __getitem__(self, item):
        return self.conf.get(item)

    def __setitem__(self, item, value):
        self.conf[item] = value

    def __len__(self):
        return len(self.conf)

    def get(self, opts, default=None, cast=None):
        return get_dict_hierarchy(self.conf, opts, default, cast)

    @property
    def view(self):
        return self.conf.copy()

    def __repr__(self):
        return f'<SettingWrapper {repr(self.conf)}>'

