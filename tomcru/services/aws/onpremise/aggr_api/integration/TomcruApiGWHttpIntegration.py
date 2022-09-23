from abc import ABCMeta, abstractmethod


class TomcruApiGWHttpIntegration(metaclass=ABCMeta):

    @abstractmethod
    def on_request(self, **kwargs):
        raise NotImplementedError()


class TomcruApiGWAuthorizerIntegration(metaclass=ABCMeta):

    @abstractmethod
    def authorize(self, evt):
        raise NotImplementedError()
