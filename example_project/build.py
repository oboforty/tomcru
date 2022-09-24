from project import project

project.debug_builders = True

project.build_app('FaaS:SAM_app', env='prod')
