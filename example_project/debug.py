import sys
from project import project

try:
    _, api_name, env = sys.argv
except:
    api_name = 'myapi'
    env = 'prod'

project.debug_builders = True
app_builder = project.app_builder('FaaS:eme_app', env=env)


#api = project.cfg.apis[api_name]

app = app_builder.build_api(api_name, env=env)
app.run(host=app.host, port=app.port, threaded=False, debug=True)
