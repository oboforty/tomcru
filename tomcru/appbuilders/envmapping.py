from ..core.cfg.proj import TomcruEnvCfg, TomcruProjectCfg


def map_env_to_appbuilder(proj, cfg: TomcruProjectCfg, envcfg: TomcruEnvCfg) -> 'InjectableAppBase':
    from .faas.InjectableAppBase import InjectableAppBase

    return InjectableAppBase(proj, cfg, envcfg)

    # if envcfg.service_type == 'faas':
    #     if envcfg.target == "aws/sam":
    #         from .faas.sam_app.SamAppBuilder import SamAppBuilder
    #         return SamAppBuilder(proj, cfg, envcfg)
    #     # elif envcfg.target == "hosted/flask":
    #     #     from .faas.flask_app.FlaskAppBuilder import FlaskAppBuilder
    #     #     return FlaskAppBuilder(proj, cfg, envcfg)
    #     elif envcfg.target == "hosted":

    # raise NotImplementedError(f'service_type={envcfg.service_type}; target={envcfg.target}')
