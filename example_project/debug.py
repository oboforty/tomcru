from project import project

project.debug_builders = True

apps, run_apps = project.build_app('FaaS:eme_app', env='dev')

run_apps(apps, env='dev')
