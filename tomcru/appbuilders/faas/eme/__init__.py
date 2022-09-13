from .EmeAppBuilder import EmeAppBuilder
from tomcru import TomCruProject


def build_app(project: TomCruProject, **kwargs):
    b = EmeAppBuilder(project, **kwargs)

    return b.build_app()
