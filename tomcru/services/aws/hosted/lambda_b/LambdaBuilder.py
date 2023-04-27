import inspect
import os
import sys
import traceback
from importlib import import_module

from tomcru.services.ServiceBase import ServiceBase
from .EmeLambdaContext import EmeLambdaContext
from tomcru import TomcruEndpointDescriptor, TomcruProject, TomcruLambdaIntegrationDescription, utils


class LambdaBuilder(ServiceBase):
    INIT_PRIORITY = 4

    def init(self):
        pass

    def inject_dependencies(self):
        """
        Injects lambda layers for all lambda integrations
        """

        # @todo: maybe we could define layers elsewhere than tomcru project config?
        _layers = self.p.cfg.layers

        if _layers:
            _layers_paths = []
            _layers_keywords = set()

            # find layers path on disk
            for layer_name, packages, folder, in_house in _layers:
                _layers_paths.append(os.path.join(self.env.app_path, 'layers', folder))
                _layers_keywords.update(packages)

            utils.inject(_layers_keywords, _layers_paths)

    def build_lambda(self, lambda_id):
        if self.object('lambda', lambda_id):
            # lambda is already built
            # todo: later: rebuild if env changes?
            return

        group, lamb = lambda_id.split('/')
        _lambd_path = os.path.join(self.env.app_path, 'lambdas', group, lamb)
        #_lambd_path = self.env.app_path

        # configure env variables
        self.set_env_for(lambda_id)

        # ensure that only local packages are loaded; and packages with the same name from other  lambdas aren't
        _ctx_orig = dict(sys.modules)

        if not os.path.exists(_lambd_path) or not os.path.exists(os.path.join(_lambd_path, 'app.py')):
            raise IOError("Lambda path does not exists: " + _lambd_path+'/app.py')

        # load lambda function
        sys.path.append(_lambd_path)
        #module = import_module(f"lambdas.{group}.{lamb}.app")
        module = import_module(f"app")
        sys.path.remove(_lambd_path)

        # restore loaded modules
        sys.modules.clear()
        sys.modules.update(_ctx_orig)

        fn = module.handler

        self.service('obj_store').add('lambda', lambda_id, fn)

        return fn

    def run_lambda(self, lamb_id, evt, **kwargs):
        lamb_fn = self.object('lambda', lamb_id)

        # prepare params
        sig = inspect.signature(lamb_fn)
        _lam_arsg = [evt]
        if len(sig.parameters) >= 2:
            _lam_arsg.append(self.get_context(self.cfg.get('settings')))

        # setup env variables
        self.set_env_for(lamb_id)

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

    def get_context(self, cfg):
        return EmeLambdaContext(cfg)

    def set_env_for(self, lamb_id):
        # inject global envvars
        for k, v in self.env.global_envvars.items():
            os.environ.setdefault(k.upper(), str(v))

        if lamb_id not in self.env.envvars_lamb:
            return

        # inject lambda specific envvars
        for k, v in self.env.envvars_lamb[lamb_id].items():
            os.environ.setdefault(k.upper(), str(v))
