from ruamel.yaml import YAML

yaml = YAML(typ='safe', pure=True)

# forces all objects to be represented in default yaml flow
yaml.default_flow_style = False
#yaml.indent(mapping=2, sequence=2, offset=2)



class Ref:
    yaml_tag = '!Ref'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_scalar(cls.yaml_tag, str(data.val))

    @classmethod
    def from_yaml(cls, constructor, node):
        # data = CommentedMap()
        # constructor.construct_mapping(node, data, deep=True)
        return cls(node.value)

    def __repr__(self):
        return self.yaml_tag+' '+self.val.__repr__()

class GetAtt:
    yaml_tag = '!GetAtt'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_scalar(cls.yaml_tag, str(data.val))

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(node.value)

    def __repr__(self):
        return self.yaml_tag+' '+self.val.__repr__()


class Join:
    yaml_tag = '!Join'

    def __init__(self, val):
        self.val = val

    @classmethod
    def to_yaml(cls, representer, data):
        return representer.represent_sequence(cls.yaml_tag, data.val)
        #return representer.represent_list(data.val)

    @classmethod
    def from_yaml(cls, constructor, node):
        # data = CommentedMap()
        array = constructor.construct_sequence(node)
        # constructor.construct_mapping(node, data, deep=True)
        return cls(array)

    def __repr__(self):
        return self.yaml_tag+' '+self.val.__repr__()


yaml.register_class(Ref)
yaml.register_class(GetAtt)
yaml.register_class(Join)


if __name__ == "__main__":
    """
    Examples to demonstrate custom tag load/dump
    """

    fefe = """
    kek:
        aid: 1
        fos: !Join
            - ""
            - - 'arn:'
              - !Ref AWS::Partition
              - ':s3:::elasticbeanstalk-*-'
              - !Ref AWS::AccountId
    """

    kek = yaml.load(fefe)

    print("yaml load:")
    print(kek)

    fe = {
        'kek': {
            'aid': 1,
            'fos': Join(["", [
                ':somearn',
                Ref('long string.asd test'),
                '/asdm/asd/asd',
                Ref('another/:ref/')
            ]])
        }
    }

    import sys
    print("yaml dump:")
    yaml.dump(fe, sys.stdout)
