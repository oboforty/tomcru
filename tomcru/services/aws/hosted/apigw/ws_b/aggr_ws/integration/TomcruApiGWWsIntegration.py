from abc import ABCMeta, abstractmethod


class TomcruApiGWWsIntegration(metaclass=ABCMeta):

    @abstractmethod
    def on_request(self, **kwargs):
        raise NotImplementedError()