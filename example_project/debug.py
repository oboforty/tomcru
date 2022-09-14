from project import project


apps, run_apps = project.build_app('FaaS:eme_app', env='dev')

run_apps(apps, env='dev')
