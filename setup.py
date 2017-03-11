from distutils.command.build import build
from setuptools import setup
from setuptools.command.install import install as _install

class install(_install):
    def run(self):
        self.run_command('build')
        _install.run(self)

setup(name="aws_ir",

      version="0.2.2",
      author="Andrew Krug, Alex McCormack, Joel Ferrier",
      author_email="andrewkrug@gmail.com,developer@amccormack.net,joel@ferrier.io",
      packages=["aws_ir", "aws_ir/libs", "aws_ir/plans", "aws_ir/plugins"],
      package_data={'aws_ir': ['templates/*.j2']},
      license="MIT",
      description="AWS Incident Response ToolKit",
      scripts=['bin/aws_ir'],
      url='https://github.com/ThreatResponse/aws_ir',

      download_url="https://github.com/ThreatResponse/aws_ir/archive/v0.2.2.tar.gz",


      use_2to3=True,
      install_requires=['boto3>=1.3.0',
                        'progressbar_latest',
                        'logutils',
                        'requests',
                        'structlog',
                        'pytz',
                        'jinja2',
                        'margaritashotgun>=0.4.0'],
      tests_require=['pytest',
                     'pytest-cov',
                     'moto',
                     'mock',
                     'magicmock'],
      )
