from threading import Thread


def start_flask_app(name, app, env, threaded=True):
    def t():
        print(f"{name} - listening on {app.host}:{app.port}")
        app.run(host=app.host, port=app.port, debug=env == 'dev' or env =='debug')

    if threaded:
        t = Thread(target=t)
        t.setDaemon(True)
        t.start()
    else:
        t()
