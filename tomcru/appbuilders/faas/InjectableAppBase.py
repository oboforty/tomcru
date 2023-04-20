from tomcru import TomcruProject, TomcruProjectCfg, TomcruEnvCfg, utils


class InjectableAppBase:

    def __init__(self, proj: TomcruProject, cfg: TomcruProjectCfg, env: TomcruEnvCfg):
        self.p = proj
        self.env = env
        self.cfg = cfg

    def __enter__(self):
        self.p.srvmgr.init_services(self.env)
        self.inject_dependencies()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deject_dependencies()

    def inject_dependencies(self):
        for srv_id, service in self.p.srvmgr:
            if hasattr(service, 'inject_dependencies'):
                service.inject_dependencies()

    def deject_dependencies(self):
        for srv_id, service in self.p.srvmgr:
            if hasattr(service, 'deject_dependencies'):
                service.inject_dependencies()

        utils.cleanup_injects()

    def service(self, serv_id):
        return self.p.srvmgr.service(self.env, serv_id)

    def object(self, srv, obj_id):
        return self.p.objmgr.get(srv, obj_id)
