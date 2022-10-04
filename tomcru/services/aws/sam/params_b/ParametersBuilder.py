import os
from collections import defaultdict

from tomcru import TomcruEndpointDescriptor, TomcruProject, TomcruLambdaIntegrationDescription


class ParametersBuilder:
    def __init__(self, project: TomcruProject, opts: dict):
        self.cfg = project.cfg
        self.opts = opts

        self.added_params = defaultdict(list)
        self.params = {}

    def store(self, idp, default_value):

        if default_value not in self.added_params[idp]:
            self.added_params[idp].append(default_value)

        idx = self.added_params[idp].index(default_value)
        return f'{idp}{idx}'

    def build_params(self):
        # todo: @later: add extra configured params (from self.opts)
        #      - and also include extra params in self.added_params to avoid collision
        params = {}

        for idp, param_items in self.added_params.items():
            L = len(param_items)

            for idx, param_value in enumerate(param_items):
                param_id = f'{idp}{idx}' if not (idx == 0 and L == 1) else idp

                params[param_id] = {
                    'Type': self.type2samtype(param_value),
                    'Default': param_value
                }

        return params

    def type2samtype(self, val):
        if isinstance(val, str): return 'String'
        elif isinstance(val, (int,float)): return 'Number'
