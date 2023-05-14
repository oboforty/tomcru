import json
from base64 import b64encode, b64decode
import os
import shutil
import signal
import subprocess

from ..LambdaHostedPyContext import LambdaHostedPyContext
from tomcru import TomcruEnvCfg

json_type = dict | list | str

def ser(o: json_type) -> str:
    return b64encode(json.dumps(o).encode('utf8')).decode('utf8')

def deser(s: str) -> json_type:
    return json.loads(b64decode(s.encode('utf8')))


class Py2NodeLambdaProxy:
    """
    This class forwards AWS lambda requests from python to a node.js executable.
    """
    def __init__(self, lambda_id: str, lambda_path: str, env: TomcruEnvCfg, pck_path, srvmgr):
        self.lambda_id = lambda_id
        self.lambda_path = lambda_path
        self.env = env

        # todo: make option to provide node path in settings
        self.node_path: str | None = None
        self.is_shell = False
        self.timeout = 5
        self.srvmgr = srvmgr
        self.boto3 = None

        self.proxy_path = os.path.join(pck_path, 'etc', 'proxies')

        # todo: verify if 'tomcru_integ' is in packages.json

    def init(self):
        # inject AWS sdk object to node_modules
        self.copy_proxy()

        if self.node_path is None:
            print("NODE PATH:", self.node_path)
            try:
                self.node_path = subprocess.check_output('which node', text=True, shell=True).rstrip()
                self.is_shell = False
            except:
                self.node_path = 'node'
                self.is_shell = True


    def deject_dependencies(self):
        self.clean_proxy()

    def __call__(self, event: dict, context: LambdaHostedPyContext, **kwargs):
        env_dict = os.environ.copy()
        cmd = [self.node_path, 't_proxy.js', ser(event)]
        if self.is_shell:
            cmd = ' '.join(cmd)

        print("calling", cmd)

        # todo: @later: pass serialzied json as binary instead of base64 between processes
        resp = None
        with subprocess.Popen(cmd, bufsize=1, universal_newlines=True, shell=self.is_shell,
                              cwd=self.lambda_path, env=env_dict,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
            for line in p.stdout:
                if line.startswith('FOO'):
                    p.stdin.write('BAR\n')
                    continue

                t_in = deser(line)

                if 'serv_id' in t_in:
                    print("  [LUAEXEC]: requesting service", t_in)
                    if 'boto3' in t_in:
                        import boto3
                        #boto3 = self.srvmgr.service(self.env, 'boto3').boto3

                        if t_in['boto3'] == 'resource':
                            srv = boto3.resource(t_in['serv_id'])

                            srv = getattr(srv, t_in['resource_type'])(t_in['resource_id'])
                        else:
                            srv = boto3.client(t_in['serv_id'])

                        serv_resp = getattr(srv, t_in['method'])(**t_in['args'])
                        p.stdin.write(ser(serv_resp)+'\n')
                    else:
                        raise NotImplementedError(t_in)
                elif 'log' in t_in:
                    print("  [LUAEXEC.LOG]:", t_in['log'])
                elif 'err' in t_in:
                    print("  [LUAEXEC.ERROR]:", t_in['err'])
                elif 'resp' in t_in:
                    resp = t_in['resp'].copy()
                elif 'bye' in t_in:
                    print("  [LUAEXEC] said GOODBYE")
                    p.send_signal(signal.SIGINT)
                    break
                else:
                    print("  [LUAEXEC] received:", line.rstrip('\n'))

            p.terminate()

        if resp:
            return resp
        else:
            raise Exception("no resp from lambda!")

    def copy_proxy(self):
        _aws = os.path.join(self.lambda_path, 'node_modules', 'aws-sdk')

        if os.path.exists(_aws):
            if os.path.exists(os.path.join(_aws, 'proxylib.js')):
                print("RM PROXY")
                shutil.rmtree(_aws)
            else:
                print("BACKUP AWS")
                # save aws sdk
                os.rename(_aws, _aws+'_tmp')

        shutil.copy(os.path.join(self.proxy_path, 't_proxy.js'), self.lambda_path)
        shutil.copytree(os.path.join(self.proxy_path, 'aws-sdk'), _aws)

    def clean_proxy(self):
        _aws = os.path.join(self.lambda_path, 'node_modules', 'aws-sdk')

        if os.path.exists(_aws):
            if os.path.exists(os.path.join(_aws, 'proxylib.js')):
                # remove AWS sdk & tomcru lambda js proxy from node_modules
                print("DELETE", _aws)
                shutil.rmtree(_aws)
            else:
                print("NOOP")

        try:
            os.remove(os.path.join(self.lambda_path, 't_proxy.js'))
        except:
            pass

        # add back aws-sdk
        try:
            os.rename(_aws+'_tmp', _aws)
        except:
            pass

    def close(self):
        self.deject_dependencies()
