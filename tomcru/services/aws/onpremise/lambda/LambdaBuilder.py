import os
import sys
from importlib import import_module

from .EmeLambdaContext import EmeLambdaContext
from tomcru import TomcruEndpointDescriptor, TomcruCfg


class LambdaBuilder:
    def __init__(self, cfg: TomcruCfg, opts: dict):
        self.cfg = cfg
        self.opts = opts

    def build_lambda(self, endpoint: TomcruEndpointDescriptor):
        if isinstance(endpoint, str):
            _endpoint = next(filter(lambda l: l[1] == endpoint, self.cfg.lambdas))
            if _endpoint is None:
                raise Exception("Lambda not found: " + endpoint)
            endpoint = _endpoint
        group, lamb, layers = endpoint

        # 1) configure env variables
        self.set_env_for(lamb)

        # 2) load lambda function
        _lambd_path = os.path.join(self.cfg.app_path, 'lambdas', group, lamb)
        sys.path.append(_lambd_path)
        module = import_module(f"lambdas.{group}.{lamb}.app")
        sys.path.remove(_lambd_path)

        return module.handler

    def get_context(self, **kwargs):
        return EmeLambdaContext(**kwargs)

    def set_env_for(self, lamb):
        if lamb not in self.cfg.envs:
            return None

        for k, v in self.cfg.envs[lamb].items():
            os.environ.setdefault(k.upper(), str(v))

        return self.cfg.envs[lamb]
