import os
from tomcru import TomcruProject

project = TomcruProject(os.path.dirname(os.path.realpath(__file__)))

with project.project_builder('test api') as tc:
    tc.add_eme_routes('myapi', integration='http')
