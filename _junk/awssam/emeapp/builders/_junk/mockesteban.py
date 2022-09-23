import os
from collections import defaultdict
import json

from botocore.exceptions import ClientError


class MockDDBResults:

    def __init__(self):
        self.cfgs = defaultdict(dict)
        self.ents = {}
        self.testCase = None
        self.user = None
        self.method = 'GET'

        self.inserts = []
        self.updates = []
        self.deletes = []
        self.accessed_table = None

    def load_real_configs(self):
        """
        this mimics the 'upload_ddb' lambda, inserting config files into a dict
        """
        path = f'{os.path.dirname(__file__)}/../admin_panel/cfg/'

        for cfg_file in os.listdir(path):
            #cfg_name = os.path.splitext(cfg_file)[0]
            with open(path+cfg_file, encoding='utf8') as fh:
                cfg = json.load(fh)

            desc = cfg.pop('__descriptor__')
            table = desc['table']

            if table == 'Config':
                # json.dumps
                cfg_name = desc.get('cfg')
                self.cfgs[table][cfg_name] = cfg
            elif table == 'CfgBoundaries':
                for v in cfg['features']:
                    v['cfg'] = v['id']
                    self.cfgs[table][v['cfg']] = v
            else:
                for k, v in cfg.items():
                    # store each key as a record
                    v['cfg'] = k
                    self.cfgs[table][v['cfg']] = v

    def assert_ent(self, _expected, entid):
        _wid, _sid = entid
        _actual = self.ents[entid]

        str0 = ['Failing attributes:']

        for k in set(_expected.keys()) | set(_actual.keys()):
            if k not in _expected:
                str0.append(f"  '{k}' not expected")
            elif k not in _actual:
                str0.append(f"  '{k}' missing")
            elif _expected[k] != _actual[k]:
                str0.append(f"  '{k}' mismatch:  {_expected[k]} != {_actual[k]}")

        str0.append('\n')
        errmsg = '\n===========================\n\n'+'\n'.join(str0)

        self.testCase.assertEqual(_expected, _actual, msg=errmsg)
        return _actual

    def assert_attr(self, attr, _expected, entid):
        _wid, _sid = entid
        _actual = self.ents[entid]

        self.testCase.assertEqual(_expected, _actual[attr])

    def assert_item(self, item, _expected, entid):
        _wid, _sid = entid
        _ent = self.ents[entid]
        amount = _ent['items'][item]

        cfg = self.get_config(item, table='Items')
        if cfg:
            if 'maxnr' in cfg:
                self.testCase.assertLessEqual(amount, cfg['maxnr'], msg=f"{item}: {amount} > max[{cfg['maxnr']}]")
            if 'minnr' in cfg:
                self.testCase.assertLessEqual(amount, cfg['minnr'], msg=f"{item}: {amount} < min[{cfg['minnr']}]")
            if 'suited' in cfg:
                self.testCase.assertTrue(esteban.check_list(_ent['stype'], cfg['suited']), msg=f"{item}: unsuited for stype {_ent['stype']}")

        self.testCase.assertEqual(_expected, amount)

    def assert_talent(self, attr, _expected, entid):
        _wid, _sid = entid
        _actual = self.ents[entid]

    def setupWorld(self, wid, isleid, seed=None, user=None, context=None, **kwargs):
        from lambdas.worlds.CreateWorld.app import handler as CreateWorld
        self.load_real_configs()

        if seed is None:
            seed = 666

        # set up initial admin user that creates the world
        self.user = {
            "uid": "adminuser",
            "username": "adminuser",
            "wid": None,
            "iso": None,
            "admin": True
        }

        resp = CreateWorld(self.event({
            'wid': wid,
            'iid': isleid,
            'seed': seed,
            **kwargs
        }), context)

        # add test supplemented user
        if user is None:
            user = {
                "uid": "testuser",
                "username": "testuser",
                "wid": 'test',
                "iso": 't_1',
                "admin": False
            }
        self.user = user

        if 'statusCode' in resp and resp['statusCode'] != 200:
            raise Exception("CreateWorld failed in SetupWorld!")
        return True

    def event(self, d):
        d['requestContext'] = {
            'http': {'method': self.method},
            'authorizer': {'lambda': {'user': self.user}}
        }
        return d


def mock_esteban(func):
    m = MockDDBResults()

    def wrapper(testCase, *args):
        m.testCase = testCase

        for mock in args:
            name = mock._extract_mock_name()

            if name == "get_config":
                mock.side_effect = m.get_config
            elif name == "get_ddb":
                mock.return_value = m
            elif name == "get_table":
                mock.side_effect = m.get_table

        func(testCase, m)
    return wrapper


class ANY:
    def __init__(self, type=None, valueset=None):
        self.type = type
        self.valueset = valueset

    def __eq__(self, other):
        ok = True
        if self.type:
            ok = isinstance(other, self.type)

        if ok and self.valueset:
            ok = other in self.valueset
        return ok

    def __repr__(self):
        if self.valueset:
            return 'ANY OF ' + str(self.valueset)
        elif self.type:
            return '-'+str(self.type.__name__)
        return '-'

ANYVALUE = ANY()
