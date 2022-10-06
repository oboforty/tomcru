import sys
from project import project
from threading import Thread

project.debug_builders = True

app_builder = project.app_builder('FaaS:eme_app')


def wt(api_name, is_main_api):
    app = app_builder.build_api(api_name, env=sys.argv[2])
    app.run(host=app.host, port=app.port, threaded=False, debug=is_main_api)

# todo:
MAIN_API = 'myapi'

assert MAIN_API in project.cfg.apis

#app_builder.build_api(*sys.argv[1:])
b_threaded: list = list(filter(lambda api_name: api_name != MAIN_API, project.cfg.apis))
b_main: str = MAIN_API


# spawn threads for the rest of apis
for api in b_threaded:
    t = Thread(target=wt, args=[api, False], daemon=True)
    t.start()

# now run main api on the main thread
wt(b_main, True)
