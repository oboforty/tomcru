import inspect
import os
import sys
import traceback
from importlib import import_module


from .EmeLambdaContext import EmeLambdaContext
from tomcru import TomcruEndpointDescriptor, TomcruProject


class LambdaBuilder:
    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.lambdas = {}

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

        fn = module.handler
        self.lambdas[lamb] = fn
        return fn

    def run_lambda(self, lamb, evt, **kwargs):
        lamb_fn = self.lambdas[lamb]

        # prepare params
        sig = inspect.signature(lamb_fn)
        _lam_arsg = [evt]
        if len(sig.parameters) >= 2:
            _lam_arsg.append(self.get_context())

        # setup env variables
        self.set_env_for(lamb)

        # execute
        try:
            resp = lamb_fn(*_lam_arsg)
        except Exception as e:
            tb = traceback.format_exc()
            raise e
            #return tuple(json.dumps({"err": str(e), "traceback": tb}), 500)

        return resp

    def get_context(self, **kwargs):
        return EmeLambdaContext(**kwargs)

    def set_env_for(self, lamb):
        if lamb not in self.cfg.envs:
            return None

        for k, v in self.cfg.envs[lamb].items():
            os.environ.setdefault(k.upper(), str(v))

        return self.cfg.envs[lamb]
