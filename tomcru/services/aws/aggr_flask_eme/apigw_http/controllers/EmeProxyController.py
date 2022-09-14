
class EmeProxyController:
    def __init__(self, group, fn_callback):
        self.group = group
        self.methods = {}
        self.general_method = fn_callback

    def __getattr__(self, item):
        if item == 'group':
            return self.group
        elif item == 'route':
            return self.group
        elif item == 'methods':
            return self.methods

        return self.general_method

    # used for eme fetching routes to method
    def __dir__(self):
        return {method: self.general_method for method in self.methods}

    def add_method(self, endpoint, lambda_fn=None):
        self.methods[endpoint.method_name] = lambda_fn
