
Development
===========

Congratulations on taking the first step to become a developer on aws_ir!
We're a very un-opinionated and forgiving community to work in.  This
guide will cover two different types of development for the aws_ir command
line interface.

Types of Development
---------------------

1. Plugins *( These are the actual incident steps. )*
2. The CLI itself

Plugins
---------------------

Plugins are probably the easiest way to get started as a developer.
Since v0.3.0 the command line interface now supports dynamically loading
plugins from source using a python module called PluginBase.

Getting Started
*****************

  First create a folder in your home directory called .awsir.  This is
  automatically searched each time awsir is run.  *Warning: If you put
  python code in here that can not be executed it will prevent your
  command line from running.*

.. code-block:: bash

    $ mkdir ~/.awsir

Excellent!  You are well on your way to creating you first plugin.

Naming your plugin
*******************

  We prefer descriptive names based on the type of resource that will be
  interacted with.  Currently aws_ir supports:

  * Host Compromises
  * Key Compromises
  * Lambda Compromises ( *Coming Soon* )
  * Role Compromises ( *Coming Soon* )

  The *TLDR* here is to name your plugin following the standard:

  * THETHINGITDOES_key.py
  * THETHINGITDOES_host.py
  * THETHINGITDOES_lambda.py
  * THETHINGITDOES_role.py

  Let's start a new plugin and we'll call it foo_key.py.

  .. code-block:: bash

      $ touch ~/.awsir/foo_key.py

Plugin Boilerplate
*******************

  Inside of that file foo_key.py there is some minimum content that has to
  exist just to get started.  All plugins follow a standard object pattern
  or they would not be plugins.

  .. code-block:: python

    import logging

    # Initializing the stream logger here ensures that any logger messages
    # bubble up into the case logs from the plugin.

    logger = logging.getLogger(__name__)

    class Plugin(object):
      def __init__(
          self,
          boto_session,
          compromised_resource,
          dry_run
      ):

          # AWS_IR generates a boto session that is handed off to each plugin.
          # This ensures as a developer you can create boto3 resource or client.
          self.session = boto_session

          # The compromised resource also gets handed of to the plugin.
          # This is slightly different depending on whether this is a
          # host of key resource.
          # See: https://github.com/ThreatResponse/aws_ir/blob/master/aws_ir/libs/compromised.py
          self.compromised_resource = compromised_resource

          # Each incident plan also sends through the type of compromise.
          # key, host, lambda, etc.
          self.compromise_type = compromised_resource['compromise_type']
          self.dry_run = dry_run

          self.access_key_id = self.compromised_resource['access_key_id']

          # The setup function should call any other private methods on the
          # object in order to achieve your IR step.  This facilitates easy
          # testing using PyUnit or PyTest.
          self.setup()

      def setup(self):
          """Method runs the plugin."""
          if self.dry_run is not True:
            # The stuff we can not dry run goes here.
            self._your_private_step()
            self._your_other_private_step()
          else:
            pass

      def validate(self):
          """Returns whether this plugin does what it claims to have done"""
          pass

      def output(self):
          """
          Future function that will be required of all plugins.  Will be
          required to contain a json schema validated payload to report on
          steps taken and assets generated.
          """
          pass

      def _your_private_step(self):
          """Something you might do as part of IR."""

          # This is how to log a status message.
          logger.info("I just secured all the things!.")
          pass

      def _your_other_private_step(self):
        """Something other thing you might do as part of IR."""
          pass

Those are the minimum required methods.  Everything you decide to do after that
in your aws_ir plugin is up to you.  As log as Plugin() is initalized, validate
is called, and output can be called the plugin will execute in the pipeline.

Considerations
*****************

You may want to get familiar with how boto sessions become boto3 resources and
clients as a part of your training. This is well documented.

`https://boto3.readthedocs.io/en/latest/reference/core/session.html <https://boto3.readthedocs.io/en/latest/reference/core/session.html>`_.

You might also want to borrow our code or pull request an aws_ir core plugin into mainstream.  We would love it if you were excited enough to do
that.

All of our plugins install from this repository: `https://github.com/ThreatResponse/aws_ir_plugins <https://github.com/ThreatResponse/aws_ir_plugins>`_.

Host Compromised Resource
**************************

The host compromised resource is a little bigger than an access key since we need to store more information to do things like interact with the VPC.
It's dictionary looks like this:

  .. code-block:: python

    "compromised_resource" : {
      "public_ip_address": "4.2.2.2",
      "private_ip_address": "10.10.10.1",
      "instance_id": "i-xxxxxxxxxxxxx",
      "launch_time": "DATETIME",
      "platform": "windows",
      "vpc_id": "vpc-xxxxxxx",
      "ami_id": "ami-xxxxxxx",
      "volume_ids": [
        "BlockDeviceMappings": []
      ],
      "region": "region"
    }

Of course your can always just print(compromised_resource) while you're developing.

Testing your plugin
***********************

There are two primary ways to test your plugin.  You can use the cli and actually
run it against an instance or key.  Or you can write a pyUnit test.

**Testing with the CLI**

1. Run the aws_ir cli help to see if your plugin is loading.

.. code-block:: bash

    $ aws_ir instance-compromise --help
    usage: aws_ir instance-compromise [-h] [--target TARGET] [--targets TARGETS]
                                      [--user USER] [--ssh-key SSH_KEY]
                                      [--plugins PLUGINS]

    optional arguments:
      -h, --help         show this help message and exit
      --target TARGET    instance-id|instance-ip
      --targets TARGETS  File of resources to process instance-id or ip-address.
      --user USER        this is the privileged ssh user for acquiring memory from
                         the instance. Required for memory only.
      --ssh-key SSH_KEY  provide the path to the ssh private key for the user.
                         Required for memory only.
      --plugins PLUGINS  Run some or all of the plugins in a custom order.
                         Provided as a comma separated list of supported plugins:
                         examineracl_host,foo_host,gather_host,isolate_host,snapsh
                         otdisks_host,stop_host,tag_host,get_memory

If you see it in the list of plugins then it's getting picked up by the plugin
loader and you can tell the cli to run only that plugin instead of a standard incident
plan. *Note: foo_host in the above output.*

**Testing with PyUnit**

If you're familiar with PyUnit you can use spulec/moto and pyUnit to test your
plugin prior to running in the CLI.  We do this for aws_ir_plugins using TravisCI.

.. code-block:: python

  # Test boilerplate for an EC2 plugin
  import boto3
  import unittest

  from aws_ir_plugins import sample_host
  from moto import mock_ec2


  class BoilerPlateTest(unittest.TestCase):
      # Begin mocking
      @mock_ec2
      def test_tag_host(self):
          # Create fake EC2 clients and sessions
          self.ec2 = boto3.client('ec2', region_name='us-west-2')
          session = boto3.Session(region_name='us-west-2')

          # Create a fake instance to process
          ec2_resource = session.resource('ec2')

          instance = ec2_resource.create_instances(
              ImageId='foo',
              MinCount=1,
              MaxCount=1,
              InstanceType='t2.medium',
              KeyName='akrug-key',
          )

          # Fake a compromised resource with the minimum set of fields needed
          self.compromised_resource = {
              'case_number': '123456',
              'instance_id': instance[0].id,
              'compromise_type': 'host'
          }

          # Execute the plugin
          plugin = sample_host.Plugin(
              boto_session=session,
              compromised_resource=self.compromised_resource,
              dry_run=False
          )

          result = plugin.validate()

          # Your test assertions

          assert result is True


I prefer to run these using nose and nose-watch during active development.
Moto ensures that you're mocking all the EC2 calls so you can develop the plugin
without effecting your AWS environment.

*Example*

.. code-block:: python

    nosetest --with-watch tests/test_sample.py

This is like guard in rails.  It watches the file system and re-runs the test
each time you write some code and save.

CLI Development
---------------------

We are currently accepting pull requests for the aws_ir cli for features and
bug fixes.

In order to develop the cli you will need to setup a python3 virtual environment.
However, you'll need to start by cloning the code.

Pulling down the code and getting started
*******************************************

Step 1. Fork us on Github.

.. code-block:: bash

  # Clone your fork

  # 1. git clone
  git@github.com:<your github here>/aws_ir.git

Step 2. Setup

  # 2. setup a virtualenv (must be python3)
  cd aws_ir
  python3 -m virtualenv env

  # 3. activate the virtualenv
  source env/bin/activate


  # 4a. with setuptools
  pip install -e .
  python setup.py test
  python setup.py pytest --addopts='tests/test_cli.py'

  -- or --

  # 4b. with local plugins and pytest-watch
  point requirements.txt to the local version of aws_ir_plugins `-e ../aws_ir_plugins`
  .. code-block:: bash
    pip3 install -r requirements.txt
    ./bin/aws_ir -h
    ptw --runner "python setup.py test"

  -- or --

  #4c. Use the docker container
  .. code-block:: bash
    docker-compose build aws_ir
    docker-compose run aws_ir bash
    pip install -e .


Step 3. Develop!


*Note:* There is a helper script in `bin/aws_ir` that can be called to execute aws_ir.

When your feature is finished simply open a PR back to us.

If you have any questions please do file a github issue
or e-mail info@threatresponse.cloud .

Using testpypi
*******************************************

.. code-block:: bash
  pip install --extra-index-url https://test.pypi.org/simple/ aws_ir==0.3.2b165

To use a test build of aws_ir_plugins:
  in setup.py:
  - point the required version at aws_ir_plugins==0.0.3b123 (substitute the build you want)
  - add: dependency_links=['https://test.pypi.org/simple/aws-ir-plugins/']


