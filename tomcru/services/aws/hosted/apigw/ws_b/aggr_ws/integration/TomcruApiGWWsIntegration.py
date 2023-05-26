from abc import ABCMeta, abstractmethod


class TomcruApiGWWsIntegration(metaclass=ABCMeta):

    @abstractmethod
    def __call__(self, base_headers: dict, **kwargs):
        raise NotImplementedError()