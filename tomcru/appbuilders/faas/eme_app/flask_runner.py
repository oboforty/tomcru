from threading import Thread


def start_flask_app(name, app, env, threaded=True):
    def t():
        app.run(host=app.host, port=app.port, debug=not threaded and (env == 'dev' or env =='debug'))

    print(f"  [S] {name} - listening on {app.host}:{app.port}")
    if threaded:
        t = Thread(target=t)
        t.setDaemon(True)
        t.start()
    else:
        t()
