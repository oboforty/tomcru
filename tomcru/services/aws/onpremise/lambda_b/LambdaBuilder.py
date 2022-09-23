import inspect
import os
import sys
import traceback
from importlib import import_module


from .EmeLambdaContext import EmeLambdaContext
from tomcru import TomcruEndpointDescriptor, TomcruProject, TomcruLambdaIntegrationDescription


class LambdaBuilder:
    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts
        self.lambdas = {}

    def build_lambda(self, endpoint: TomcruLambdaIntegrationDescription):
        if isinstance(endpoint, str):

            print(1)
        #     _endpoint = next(filter(lambda l: l[1] == endpoint, self.cfg.lambdas))
        #     if _endpoint is None:
        #         raise Exception("Lambda not found: " + endpoint)
        #     endpoint = _endpoint

        # 1) configure env variables
        self.set_env_for(endpoint.lambda_id)

        # 2) load lambda function
        _lambd_path = os.path.join(self.cfg.app_path, 'lambdas', endpoint.group, endpoint.lamb)
        sys.path.append(_lambd_path)
        module = import_module(f"lambdas.{endpoint.group}.{endpoint.lamb}.app")
        sys.path.remove(_lambd_path)

        fn = module.handler
        self.lambdas[endpoint.lambda_id] = fn
        return fn

    def run_lambda(self, lamb_id, evt, **kwargs):
        lamb_fn = self.lambdas[lamb_id]

        # prepare params
        sig = inspect.signature(lamb_fn)
        _lam_arsg = [evt]
        if len(sig.parameters) >= 2:
            _lam_arsg.append(self.get_context())

        # setup env variables
        self.set_env_for(lamb_id)

        # setup layers
        # @TODO: ITT
        # todo         - tomcru utils: MyMetaFinder
        # todo         - tomcru utils: lib replacer
        # todo         - boto3 inject service
        # todo         - inject layers (here)

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

    def set_env_for(self, lamb_id):
        if lamb_id not in self.cfg.envs:
            return None

        for k, v in self.cfg.envs[lamb_id].items():
            os.environ.setdefault(k.upper(), str(v))

        return self.cfg.envs[lamb_id]
