from threading import Thread


def start_flask_app(name, app_builder, addr):
    def t():
        host, port = addr.split(':')

        app = app_builder()

        print(name, " - listening on:", addr)
        app.run(host=host, port=port.strip('/'), debug=False, use_reloader=False)

    t = Thread(target=t)
    t.setDaemon(True)
    t.start()
