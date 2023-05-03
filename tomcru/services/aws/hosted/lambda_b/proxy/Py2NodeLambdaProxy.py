import json
from base64 import b64encode, b64decode
import os
import shutil
import subprocess

from ..LambdaHostedPyContext import LambdaHostedPyContext
from tomcru import TomcruEnvCfg


class Py2NodeLambdaProxy:
    """
    This class forwards AWS lambda requests from python to a node.js executable.
    """
    def __init__(self, lambda_id: str, lambda_path: str, env: TomcruEnvCfg, pck_path):
        self.lambda_id = lambda_id
        self.lambda_path = lambda_path
        self.env = env

        # todo: make option to provide node path in settings
        self.node_path: str | None = None

        # todo: verify if 'tomcru_integ' is in packages.json

        self.proxy_file_name = 't_proxy.js'
        self.proxy_file = os.path.join(self.env.spec_path, 'lambdas/_proxies', self.proxy_file_name)
        if not os.path.exists(self.proxy_file):
            self.proxy_file = os.path.join(pck_path, 'etc', 'proxies', self.proxy_file_name)

    def init(self):
        # inject AWS sdk object to node_modules
        # @todo

        # inject tomcru lambda js proxy
        shutil.copy(self.proxy_file, self.lambda_path)

        if self.node_path is None:
            print("NODE PATH:", self.node_path)
            try:
                self.node_path = subprocess.check_output('which node', text=True, shell=True).rstrip()
            except:
                self.node_path = 'node'

    def deject_dependencies(self):
        # remove AWS sdk & tomcru lambda js proxy from node_modules
        fn = os.path.join(self.lambda_path, self.proxy_file_name)

        if os.path.exists(fn):
            os.remove(fn)

    def __call__(self, event: dict, context: LambdaHostedPyContext, **kwargs):
        env_dict = os.environ.copy()#dict(os.environ)

        # todo: @later: pass serialzied json as binary instead of base64 between processes
        #, _ = os.path.splitext(self.proxy_file)

        event_ser = b64encode(json.dumps(event).encode('utf8')).decode('utf8')

        cmd = ' '.join([self.node_path, 't_proxy.js', event_ser])

        try:
            result_b64 = subprocess.check_output(cmd,
                                                 # capture_output=True,
                                                 text=True, shell=True,
                                                 universal_newlines=True,
                                                 # stderr=subprocess.STDOUT,
                                                 env=env_dict,
                                                 timeout=1,
                                                 cwd=self.lambda_path)
            try:
                result = json.loads(b64decode(result_b64.encode('utf8')))

                return result
            except:
                result = result_b64
        except subprocess.CalledProcessError as e:
            result = "err " + str(e.stderr)

        return {
            "result": str(result)
        }


    def close(self):
        self.deject_dependencies()
