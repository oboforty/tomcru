
class EmeProxyController:
    def __init__(self, group, apiopts, on_request):
        self.group = group
        self.methods = {}
        self.on_request = on_request
        self.api_root = apiopts.get('api_root')

    def __getattr__(self, item):
        if item == 'group':
            return self.group
        elif item == 'route':
            return self.group
        elif item == 'methods':
            return self.methods

        return self.on_request

    # used for eme fetching routes to method
    def __dir__(self):
        return {method: self.on_request for method in self.methods}

    def add_method(self, endpoint, fn):
        self.methods[endpoint.method_name] = fn
