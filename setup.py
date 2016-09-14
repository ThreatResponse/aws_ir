from distutils.command.build import build
from setuptools import setup
from setuptools.command.install import install as _install

class install(_install):
    def run(self):
        self.run_command('build')
        _install.run(self)

setup(name="aws_ir",
      version="0.1.0",
      author="Andrew Krug, Alex McCormack, Joel Ferrier",
      author_email="andrewkrug@gmail.com,alex@example.com,joel@ferrier.io",
      packages=["aws_ir", "aws_ir/libs"],
      license="MIT",
      description="AWS Incident Response ToolKit",
      scripts=['bin/aws_ir'],
      use_2to3=True,
      install_requires=['pytest==2.9.1',
                        'boto3==1.3.0',
                        'progressbar_latest==2.4.0',
                        'requests',
                        'structlog',
                        'pytz',
                        'margaritashotgun>=0.3.1'],
      tests_require=['pytest'],
      )
