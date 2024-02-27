from setuptools import setup


setup(name='tomcru',
      version='1.0.0',
      description='Multi-purpose web framework',
      url='https://github.com/doorskgs/tomcru',
      author='oboforty',
      author_email='rajmund.csombordi@hotmail.com',
      license='MIT',
      zip_safe=False,
      packages=['tomcru'],
      install_requires=[
            "prance>=0.22,<1.0",
            "apispec>=6.3,<7.0",
            "openapi-spec-validator>=0.5,<1.0",
            "flask-swagger-ui>=4.11,<5.0",
            "pyjwt[crypto]>=2.6,<3.0",
            "requests>=2.28,<3.0",
            "botocore>=1.29,<2.0",
            "pyyaml==6.0",
            "flatten-json==0.1.13",
            "deepmerge==1.1.0",
            "tabulate==0.9.0",
            "tomcru-jerry[static]",
      ])
