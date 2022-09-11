import os
from tomcru import TomCruProject

project = TomCruProject(os.path.dirname(os.path.realpath(__file__)))

with project.project_builder('petstore') as tc:
    tc.add_openapi_routes('petstore', integration='http')
