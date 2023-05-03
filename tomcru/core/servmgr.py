import os

from .cfg.proj import TomcruEnvCfg
from .modloader import load_serv
from .utils import SettingWrapper


class ServiceManager:

    def __init__(self, p, objmgr):
        self.p = p
        self.objmgr = objmgr

    def load_services(self, env):
        return list(map(lambda serv_id: self.service(env, serv_id), self.configured_services(env)))

    def service(self, env: TomcruEnvCfg, serv_id):
        if serv_id == 'obj_store_b' or serv_id == 'obj_store':
            # special service: internal object store
            return self.objmgr

        srv = self.objmgr.get('srv', serv_id)

        if not srv:
            pck_path = self.p.cfg.pck_path
            serv_opts = env.serv_opts.get(serv_id, SettingWrapper({}))

            target = env.target.split('/')

            # this option specifies which library to use e.g. flask vs fastapi for apigw
            if target_solution := serv_opts.get('service', {}).get('target'):
                target.append(serv_id)
                module_name = target_solution + '_b'
            else:
                module_name = serv_id + '_b'

            # load service config
            search_path = os.path.join(pck_path, 'services', env.vendors[0], *target)

            # try:
            srv_builder = load_serv(search_path, module_name, debug=self.p.debug)
                # print("        OKOK", module_name, search_path)
            # except ModuleNotFoundError:
            #     print("        NOK", module_name, search_path)
            #    raise Exception("Service not found: " + module_name)

            # some services can have zero config
            serv_opts.conf['__fileloc__'] = os.path.dirname(search_path)
            serv_cfg = self.p.cfg.services.get(serv_id, SettingWrapper({}))

            if hasattr(srv_builder, 'create_builder'):
                srv = srv_builder.create_builder(self.p, serv_cfg, serv_opts, env)
            else:
                srv = srv_builder
            self.objmgr.add('srv', serv_id, srv)

        return srv

    def __iter__(self):
        return self.objmgr.iter_services()

    def configured_services(self, env: TomcruEnvCfg):
        return set(self.p.cfg.services.keys()) | set(env.serv_opts.keys())
