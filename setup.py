from setuptools import setup


setup(name='tomcru',
      version='0.2.0',
      description='Multi-purpose web framework',
      url='https://github.com/doorskgs/tomcru',
      author='oboforty',
      author_email='rajmund.csombordi@hotmail.com',
      license='MIT',
      zip_safe=False,
      packages=['tomcru'],
      #package_data={'awssam/tpl': ['fragments/*.yml', '*.yml']},
      # entry_points={
      #     'console_scripts': [
      #         'eme = eme._tools.cli:main',
      #     ],
      # },
      install_requires=[
          #'eme',
      ])
