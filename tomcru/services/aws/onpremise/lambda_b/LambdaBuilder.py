import inspect
import os
import sys
import traceback
from importlib import import_module


from .EmeLambdaContext import EmeLambdaContext
from tomcru import TomcruEndpointDescriptor, TomcruProject, TomcruLambdaIntegrationDescription
from tomcru import utils


class LambdaBuilder:
    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.layers = {}
        self.objs = project.serv('aws:onpremise:obj_store')

    def init(self):
        pass

    def inject_dependencies(self):
        """
        Injects lambda layers for all lambda integrations
        """

        if self.cfg.layers:
            # find layers path on disk
            _layers_paths = list(map(lambda f: os.path.join(self.cfg.app_path, 'layers', f[3]), self.cfg.layers))
            _layers_keywords = set(map(lambda f: f[1][0], self.cfg.layers))
            utils.inject(_layers_keywords, _layers_paths)

    def build_lambda(self, lambda_id, env: str):
        if self.objs.has('lambda', lambda_id):
            # lambda is already built
            # todo: later: rebuild if env changes?
            return

        group, lamb = lambda_id.split('/')
        _lambd_path = os.path.join(self.cfg.app_path, 'lambdas', group, lamb)

        # configure env variables
        self.set_env_for(lambda_id, env)

        # ensure that only local packages are loaded; and packages with the same name from other  lambdas aren't
        _ctx_orig = dict(sys.modules)

        if not os.path.exists(_lambd_path) or not os.path.exists(os.path.join(_lambd_path, 'app.py')):
            raise IOError("Lambda path does not exists: " + _lambd_path+'/app.py')

        # load lambda function
        sys.path.append(_lambd_path)
        module = import_module(f"lambdas.{group}.{lamb}.app")
        sys.path.remove(_lambd_path)

        # restore loaded modules
        sys.modules.clear()
        sys.modules.update(_ctx_orig)

        fn = module.handler

        self.objs.add('lambda', lambda_id, fn)
        return fn

    def run_lambda(self, lamb_id, evt, env, **kwargs):
        lamb_fn = self.objs.get('lambda', lamb_id)

        # prepare params
        sig = inspect.signature(lamb_fn)
        _lam_arsg = [evt]
        if len(sig.parameters) >= 2:
            _lam_arsg.append(self.get_context())

        # setup env variables
        self.set_env_for(lamb_id, env)

        # setup layers
        # todo: inject individual layers

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

    def set_env_for(self, lamb_id, env):
        _envs = self.cfg.envs[env]

        if lamb_id not in _envs:
            return None

        for k, v in _envs[lamb_id].items():
            os.environ.setdefault(k.upper(), str(v))

        return _envs[lamb_id]
