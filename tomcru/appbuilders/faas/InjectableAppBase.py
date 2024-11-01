import logging

from tomcru.core import utils

logger = logging.getLogger('tomcru')


class InjectableAppBase:

    def __init__(self, proj: 'TomcruProject', cfg: 'TomcruProjectCfg', env: 'TomcruEnvCfg'):
        self.p = proj
        self.env = env
        self.cfg = cfg

        self.inited = False

    def __enter__(self):
        if not self.inited:
            self.p.srvmgr.load_services(self.env)

        for serv_id, service in self.p.srvmgr:
            if hasattr(service, 'inject_dependencies'):
                service.inject_dependencies()

        if not self.inited:
            self.inited = True

            for serv_id, service in sorted(self.p.srvmgr, key=lambda s: s[1].INIT_PRIORITY):
                if hasattr(service, 'init'):
                    logger.debug(f"[{serv_id}] initializing (ENV={self.env.env})")
                    service.init()
                else:
                    logger.debug(f"[{serv_id}] skipped init (ENV={self.env.env})")

        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        for serv_id, service in self.p.srvmgr:
            if hasattr(service, 'deject_dependencies'):
                service.deject_dependencies()

        utils.cleanup_injects()

    def service(self, serv_id):
        return self.p.srvmgr.service(self.env, serv_id)

    def object(self, srv, obj_id):
        return self.p.objmgr.get(srv, obj_id)

    def __repr__(self):
        return f'<InjectableAppBase env={self.env.env_id} target={self.env.target} service_type={self.env.service_type} path={self.env.app_path}>'