from ..services.dal.boto3 import Boto3
b3: Boto3

class Boto3Loader(Loader):
    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        global b3
        return b3

    def exec_module(self, module):
        return
        with open(self.filename) as f:
            data = f.read()

        # manipulate data some way...

        exec(data, vars(module))

_registered_finders = []

def install(app, app_path, layers):
    global b3, _registered_finders
    """Inserts the finder into the import machinery"""

    __PATH__ = os.path.dirname(os.path.realpath(__file__))

    # custom loader to replace esteban boto3 dependency
    sys.meta_path.insert(0, f:= MyMetaFinder('boto3', __PATH__ + '/../services/dal', Boto3Loader))
    _registered_finders.append(f)

    # custom loader to replace
    if layers:

        #__PATH__
        sys.meta_path.insert(0, f:= MyMetaFinder(_layers_keywords, _layers_paths))
        _registered_finders.append(f)

    b3 = Boto3(app, app_path)

    return b3

def uninstall():
    """Inserts the finder into the import machinery"""
