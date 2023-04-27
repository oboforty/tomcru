import inspect
import sys
import ast
from collections import defaultdict

from thecode import func
# class ObjType:
#     def __init__(self):
#         self.kekeke: float = 123
#faszkivan = 53

params = inspect.get_annotations(func)
_src = inspect.getsource(func)
cv_root = ast.parse(_src)
#p = inspect.getsource(func)
#cv = inspect.getclosurev ars(func)

event_param_name = list(params.keys())[0]

#print(type(node))
_ast_per_line = defaultdict(list)
for node in ast.walk(cv_root):
    _name = ''

    if hasattr(node, 'id'): _name = node.id
    elif hasattr(node, 'annotation'): _name = node.annotation.id if hasattr(node.annotation, 'id') else type(node)
    elif hasattr(node, 'id'): _name = node.id
    elif hasattr(node, 'id'): _name = node.id
    else: _name = '['+str(type(node))+']'

    print(_name)
    #if not isinstance(node, (ast.Module, ast.arguments)):
    #    _ast_per_line[node.lineno].append(node)
sys.exit()

# variables that spawn from event
_watches = {event_param_name}

mk = max(_ast_per_line.keys())
for i in range(mk):
    print(f'[{i}]', end='    ')

    for node in _ast_per_line[i]:

        if isinstance(node, ast.Store):
            print(list(node.__dict__.keys()), end=' ')
        # if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        #     #if node.id in _watches:
        #     print(node.value, node.slice.value, end=' ')

    print('')
