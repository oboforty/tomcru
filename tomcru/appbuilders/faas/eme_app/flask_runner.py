from threading import Thread


def start_flask_app(name, app, host, port):
    def t():
        print(f"{name} - listening on {host}:{port}")
        app.run(host=host, port=port.strip('/'), debug=False, use_reloader=False)

    t = Thread(target=t)
    t.setDaemon(True)
    t.start()
