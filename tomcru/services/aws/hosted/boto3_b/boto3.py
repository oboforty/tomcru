
class Boto3:
    __TOMCRU__ = True

    def __init__(self, objgetter, allowed_clients, allowed_resources):
        self._objs_getter = objgetter
        self.allowed_clients = allowed_clients
        self.allowed_resources = allowed_resources

    def client(self, resname, **kwargs):
        assert resname in self.allowed_clients

        _obj = self._objs_getter(resname)
        # if hasattr(_obj, 'as_boto3_resource'):
        #     return _obj.as_boto3_resource(**kwargs)
        return _obj

    def resource(self, resname, **kwargs):
        assert resname in self.allowed_resources

        _obj = self._objs_getter(resname)
        # if hasattr(_obj, 'as_boto3_resource'):
        #     return _obj.as_boto3_resource(**kwargs)
        return _obj

    def Session(self):
        return self
