
Quickstart
==========

First, :doc:`Install aws_ir <installing>`.

Installation
************

.. code-block:: bash

    $ python3 -m virtualenv env
    $ source/env/bin/activate
    $ pip install aws_ir

For other installation options see: `installing <https://aws_ir.readthedocs.io/en/latest/installing.html>`__.

AWS Credentials
***************

Ensure aws credentials are configured under the user running aws_ir as documented `by amazon <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`__.


Setup Roles with Cloudformation
*************************************

A cloudformation stack has been provided to setup a group and a responder role.

Simply create the stack available at:

`https://github.com/ThreatResponse/aws_ir/blob/master/cloudformation/responder-role.yml <https://github.com/ThreatResponse/aws_ir/blob/master/cloudformation/responder-role.yml>`_.

Then add all your users to the IncidentResponders group.  After that you're good to go!

*Note that this roles has a constraint that all your responders use MFA.*
.. code-block:: bash
  aws:MultiFactorAuthPresent: 'true'


Key Compromise
**************

The ``aws_ir`` subcommand ``key-compromise`` disables access keys in the case of a key compromise.
It's single argument is the access key id, he compromised key is disabled via the AWS api.

.. code-block:: bash

   usage: aws_ir key-compromise [-h] --access-key-id ACCESS_KEY_ID
                                [--plugins PLUGINS]

   optional arguments:
     -h, --help            show this help message and exit
     --access-key-id ACCESS_KEY_ID
     --plugins PLUGINS     Run some or all of the plugins in a custom order.
                           Provided as a comma separated listSupported plugins:
                           disableaccess_key,revokests_key

Below is the output of running the ``key-compromise`` subcommand.

.. code-block:: bash

    $ aws_ir key-compromise --access-key-id AKIAINLHPIG64YJXPK5A
    2017-07-20T21:04:01 - aws_ir.cli - INFO - Initialization successful proceeding to incident plan.
    2017-07-20T21:04:01 - aws_ir.plans.key - INFO - Attempting key disable.
    2017-07-20T21:04:03 - aws_ir.plans.key - INFO - STS Tokens revoked issued prior to NOW.
    2017-07-20T21:04:03 - aws_ir.plans.key - INFO - Disable complete.  Uploading results.
    Processing complete for cr-17-072104-7d5f
    Artifacts stored in s3://cloud-response-9cabd252416b4e5a893395c533f340b7


Instance Compromise
*******************

The ``aws_ir`` subcommand ``instance-compromise`` preserves forensic artifacts from a compromised instance after isolating the instance.
Once all artifacts are collected and tagged the compromised instance is powered off.
The ``instance-compromise`` subcommand takes three arguments, the ``instance-ip`` of the compromised instance, a ``user`` with ssh access to the target instance, and the ``ssh-key`` used for authentication.

Currently ``user`` must be capable of passwordless sudo for memory capture to complete.  If ``user`` does not have passwordless sudo capabilities all artifiacts save for the memory capture will be gathered.

.. code-block:: bash
   $ aws_ir instance-compromise -h
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
                        examineracl_host,gather_host,isolate_host,snapsh
                        otdisks_host,stop_host,tag_host,get_memory

.. note:: AWS IR saves all forensic artifacts except for disk snapshots in an s3 bucket created for each case.  Disk snapshots are tagged with the same case number as the rest of the rest of the artifacts.

Below is the output of running the ``instance-compromise`` subcommand.

.. code-block:: bash

   $  aws_ir --examiner-cidr-range '4.4.4.4/32' instance-compromise --target 52.40.162.126 --user ec2-user --ssh-key ~/Downloads/testing-041.pem
      2017-07-20T21:10:50 - aws_ir.cli - INFO - Initialization successful proceeding to incident plan.
      2017-07-20T21:10:50 - aws_ir.libs.case - INFO - Initial connection to AmazonWebServices made.
      2017-07-20T21:11:03 - aws_ir.libs.case - INFO - Inventory AWS Regions Complete 14 found.
      2017-07-20T21:11:03 - aws_ir.libs.case - INFO - Inventory Availability Zones Complete 37 found.
      2017-07-20T21:11:03 - aws_ir.libs.case - INFO - Beginning inventory of resources world wide.  This might take a minute...
      2017-07-20T21:11:03 - aws_ir.libs.inventory - INFO - Searching ap-south-1 for instance.
      2017-07-20T21:11:05 - aws_ir.libs.inventory - INFO - Searching eu-west-2 for instance.
      2017-07-20T21:11:05 - aws_ir.libs.inventory - INFO - Searching eu-west-1 for instance.
      2017-07-20T21:11:06 - aws_ir.libs.inventory - INFO - Searching ap-northeast-2 for instance.
      2017-07-20T21:11:07 - aws_ir.libs.inventory - INFO - Searching ap-northeast-1 for instance.
      2017-07-20T21:11:08 - aws_ir.libs.inventory - INFO - Searching sa-east-1 for instance.
      2017-07-20T21:11:09 - aws_ir.libs.inventory - INFO - Searching ca-central-1 for instance.
      2017-07-20T21:11:09 - aws_ir.libs.inventory - INFO - Searching ap-southeast-1 for instance.
      2017-07-20T21:11:10 - aws_ir.libs.inventory - INFO - Searching ap-southeast-2 for instance.
      2017-07-20T21:11:11 - aws_ir.libs.inventory - INFO - Searching eu-central-1 for instance.
      2017-07-20T21:11:12 - aws_ir.libs.inventory - INFO - Searching us-east-1 for instance.
      2017-07-20T21:11:13 - aws_ir.libs.inventory - INFO - Searching us-east-2 for instance.
      2017-07-20T21:11:13 - aws_ir.libs.inventory - INFO - Searching us-west-1 for instance.
      2017-07-20T21:11:13 - aws_ir.libs.inventory - INFO - Searching us-west-2 for instance.
      2017-07-20T21:11:14 - aws_ir.libs.case - INFO - Inventory complete.  Proceeding to resource identification.
      2017-07-20T21:11:14 - aws_ir.plans.host - INFO - Proceeding with incident plan steps included are ['gather_host', 'isolate_host', 'tag_host', 'snapshotdisks_host', 'examineracl_host', 'get_memory', 'stop_host']
      2017-07-20T21:11:14 - aws_ir.plans.host - INFO - Executing step gather_host.
      2017-07-20T21:11:15 - aws_ir.plans.host - INFO - Executing step isolate_host.
      2017-07-20T21:11:16 - aws_ir.plans.host - INFO - Executing step tag_host.
      2017-07-20T21:11:17 - aws_ir.plans.host - INFO - Executing step snapshotdisks_host.
      2017-07-20T21:11:17 - aws_ir.plans.host - INFO - Executing step examineracl_host.
      2017-07-20T21:11:19 - aws_ir.plans.host - INFO - Executing step get_memory.
      2017-07-20T21:11:19 - aws_ir.plans.host - INFO - attempting memory run
      2017-07-20T21:11:19 - aws_ir.plans.host - INFO - Attempting run margarita shotgun for ec2-user on 52.40.162.126 with /Users/akrug/Downloads/testing-041.pem
      2017-07-20T21:11:21 - margaritashotgun.repository - INFO - downloading https://threatresponse-lime-modules.s3.amazonaws.com/modules/lime-4.9.32-15.41.amzn1.x86_64.ko as lime-2017-07-21T04:11:21-4.9.32-15.41.amzn1.x86_64.ko
      2017-07-20T21:11:25 - margaritashotgun.memory - INFO - 52.40.162.126: dumping memory to s3://cloud-response-a0f2d7e68ef44c36a79ccfe4dcef205a/52.40.162.126-2017-07-21T04:11:19-mem.lime
      2017-07-20T21:15:43 - margaritashotgun.memory - INFO - 52.40.162.126: capture 10% complete
      2017-07-20T21:19:37 - margaritashotgun.memory - INFO - 52.40.162.126: capture 20% complete
      2017-07-20T21:23:41 - margaritashotgun.memory - INFO - 52.40.162.126: capture 30% complete
      2017-07-20T21:28:17 - margaritashotgun.memory - INFO - 52.40.162.126: capture 40% complete
      2017-07-20T21:32:42 - margaritashotgun.memory - INFO - 52.40.162.126: capture 50% complete
      2017-07-20T21:37:18 - margaritashotgun.memory - INFO - 52.40.162.126: capture 60% complete
      2017-07-20T21:39:18 - margaritashotgun.memory - INFO - 52.40.162.126: capture 70% complete
      2017-07-20T22:00:13 - margaritashotgun.memory - INFO - 52.40.162.126: capture 80% complete
      2017-07-20T22:04:19 - margaritashotgun.memory - INFO - 52.40.162.126: capture 90% complete
      2017-07-20T22:17:32 - margaritashotgun.memory - INFO - 52.40.162.126: capture 100% complete
      2017-07-20T21:41:52 - aws_ir.plans.host - INFO - memory capture completed for: ['52.40.162.126'], failed for: []
      2017-07-20T21:41:52 - aws_ir.plans.host - INFO - Executing step stop_host.

   Processing complete for cr-17-072104-7d5f
   Artifacts stored in s3://cloud-response-a0f2d7e68ef44c36a79ccfe4dcef205a

Note that ``aws_ir instance-compromise`` installs `margarita shotgun <https://margaritashotgun.readthedocs.io/en/latest/>`__ on your local machine to perform memory capture. Doing so requires trusting the GPG key of security@threatresponse.cloud, which can be done with the command:

.. code:: bash

   $ curl -s https://threatresponse-lime-modules.s3.amazonaws.com/REPO_SIGNING_KEY.asc | gpg --import -
   gpg: key 67172B17: public key "Lime Signing Key (Threat Response Official Lime Signing Key) <security@threatresponse.cloud>" imported
   gpg: Total number processed: 1
   gpg:               imported: 1  (RSA: 1)
