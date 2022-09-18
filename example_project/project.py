import os
from tomcru import TomcruProject

project = TomcruProject(os.path.dirname(os.path.realpath(__file__)))

with project.project_builder('test api') as tc:
    tc.parse_project_apis()
