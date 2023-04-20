

class ObjStore:
    """
    Stores both
        - cloud objects (e.g. if in hosted FaaS environemnt)
        - service references for Tomcru project
    """

    def __init__(self, p, use_cache=False):
        self.p = p
        self.objects = {}

        # todo: add -optional- LRU cache?

    def get(self, serv, obj_id):
        return self.objects.get(serv + ':' + obj_id)

    def add(self, serv, obj_id, obj):
        self.objects[serv + ':' + obj_id] = obj

    def has(self, serv, obj_id):
        return serv + ':' + obj_id in self.objects

    def list(self):
        return list(self.objects.keys())

    def __iter__(self):
        return iter(self.objects.items())

    def iter_services(self):
        for _key, obj in self.objects.items():
            if _key.startswith('srv:'):
                yield _key[4:], obj
