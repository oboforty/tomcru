from abc import ABCMeta, abstractmethod

from tomcru import TomcruApiAuthorizerDescriptor


class TomcruApiGWHttpIntegration(metaclass=ABCMeta):

    @abstractmethod
    def on_request(self, **kwargs):
        raise NotImplementedError()


class TomcruApiGWAuthorizerIntegration(metaclass=ABCMeta):

    def __init__(self, cfg: TomcruApiAuthorizerDescriptor):
        self.cfg = cfg
        self.authorizers_cache = {}

    def get_cache(self, cache_key):
        return self.authorizers_cache.get(cache_key) if cache_key else None

    def set_cache(self, cache_key, cache_result):
        self.authorizers_cache[cache_key] = cache_result

    @abstractmethod
    def authorize(self, evt):
        raise NotImplementedError()
