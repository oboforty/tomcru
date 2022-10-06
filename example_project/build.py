import sys

from project import project

try:
    _, env = sys.argv
except:
    env = 'prod'

project.debug_builders = True

app_builder = project.app_builder('FaaS:SAM_app', env=env)

app_builder.build_app(env=env)
