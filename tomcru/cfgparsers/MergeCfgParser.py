import os

from tomcru import TomcruSubProjectCfg


class MergeCfgParser:
    def __init__(self, cfgparser, name):
        self.cfg = cfgparser.cfg
        self.cfg_name = name
        self.cfgs: dict[str, TomcruSubProjectCfg] = cfgparser.proj.cfgs

        self.marked_merges = []

    def merge_into(self, cfg_name):
        if self.cfg_name == cfg_name:
            raise f"Can't merge into self: {cfg_name}"

        self.marked_merges.append((cfg_name, self.cfg_name))

    def merge(self, cfg_name):
        if self.cfg_name == cfg_name:
            raise f"Can't merge into self: {cfg_name}"

        self.marked_merges.append((self.cfg_name, cfg_name))

    def base_from(self, cfg_name):
        """
        Immediately merges specified config into this one
        :param cfg_name:
        :return:
        """
        if self.cfg_name == cfg_name:
            raise f"Can't merge into self: {cfg_name}"

        self.cfgs[self.cfg_name].update(self.cfgs[cfg_name])

    def do_merge(self):
        for cfg1_name, cfg2_name in self.marked_merges:
            self.cfgs[cfg1_name].update(cfg2_name)

        self.marked_merges.clear()
