import re
from distutils.command.build import build
from setuptools import setup

VERSION = re.search(
    r"^__version__ = ['\"]([^'\"]*)['\"]",
    open('aws_ir/_version.py', 'r').read(),
    re.MULTILINE
).group(1)

setup(name="aws_ir",
      version=VERSION,
      author="Andrew Krug, Alex McCormack, Joel Ferrier, Jeff Parr",
      author_email="andrewkrug@gmail.com,developer@amccormack.net,joel@ferrier.io",
      packages=["aws_ir", "aws_ir/libs", "aws_ir/plans"],
      license="MIT",
      description="AWS Incident Response ToolKit",
      scripts=['bin/aws_ir'],
      url='https://github.com/ThreatResponse/aws_ir',
      download_url="https://github.com/ThreatResponse/aws_ir/archive/v0.3.0.tar.gz",
      use_2to3=True,
      zip_safe=True,
      install_requires=['boto3>=1.3.0',
                        'progressbar_latest',
                        'logutils==0.3.3',
                        'requests',
                        'structlog',
                        'pytz',
                        'jinja2',
                        'pluginbase',
                        'margaritashotgun>=0.4.1',
                        'aws-ir-plugins>=0.0.3'
                        ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest',
                     'pytest-cov',
                     'pytest-watch',
                     'moto',
                     'mock'],
      )
