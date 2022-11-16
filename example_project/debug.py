import sys
from project import project

try:
    _, api_name, env = sys.argv
except:
    api_name = 'myapi'
    env = 'prod'

project.debug_builders = True
app_builder = project.app_builder('FaaS:eme_app', env=env)

app_builder.init_services()
app_builder.inject_dependencies()

app = app_builder.build_api(api_name, env=env)

app_builder.deject_dependencies()

app.run(host=app.host, port=app.port, threaded=False, debug=True)
