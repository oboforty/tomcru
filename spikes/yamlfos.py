from io import StringIO
import yaml
from yaml import Dumper
from yaml import YAMLObjectMetaclass


class Ref(yaml.YAMLObject):
    yaml_tag = '!Ref'

    def __init__(self, val):
        self.val = val

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)

    @classmethod
    def to_yaml(cls, dumper: yaml.Dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.val)

    def __repr__(self):
        return self.yaml_tag+' '+self.val.__repr__()


class GetAtt(yaml.YAMLObject):
    yaml_tag = '!GetAtt'

    def __init__(self, val):
        self.val = str(val)

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)

    @classmethod
    def to_yaml(cls, dumper: yaml.Dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.val)

    def __repr__(self):
        return self.yaml_tag+' '+self.val.__repr__()

fstr = """
kek:
  aid: 1
  fos: !Ref 'tesomsz.arn'
  szar: !GetAtt 'tesomsz.arn'
"""

sio = StringIO()


eee = yaml.load(fstr, Loader=yaml.Loader)
print(eee)
