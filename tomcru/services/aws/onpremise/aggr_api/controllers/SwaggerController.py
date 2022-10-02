

class SwaggerController:
    def __init__(self, server):
        self.server = server
        self.group = "Swagger"

    def get_swagger(self):
        return "Hello there"

    def get_swagger_ui(self):
        return "Hello there"
