

class HomeController:
    def __init__(self, server):
        self.server = server
        self.group = "Home"

        # self.server.setRouting({
        # })

    def index(self):
        return "Hello there"
