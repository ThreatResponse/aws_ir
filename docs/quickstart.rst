
Quickstart
==========

First, :doc:`Install aws_ir <installing>`.

Installation
************

``pip install aws_ir``

Or see `installing <https://aws_ir.readthedocs.io/en/latest/installing.html>`__.

AWS Credentials
***************

Ensure aws credentials are configured under the user running aws_ir as documented `by amazon <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`__.

.. note:: Check back soon for an IAM policy featuring the minimum set of required permissions

Key Compromise
**************

The ``aws_ir`` subcommand ``key-compromise`` disables access keys in the case of a key compromise.
It's single argument is the access key id, he compromised key is disabled via the AWS api.

.. code-block:: bash

   $ aws_ir key-compromise -h
   usage: aws_ir key_compromise [-h] --access-key-id ACCESS_KEY_ID
   
   optional arguments:
     -h, --help            show this help message and exit
     --access-key-id ACCESS_KEY_ID

Below is the output of running the ``key-compromise`` subcommand.

.. code-block:: bash

   $ aws_ir key_compromise --access-key-id AKIAJGOVL2FIYOG6YFIA
   2016-07-29 16:53:35,458 - aws_ir.cli - INFO - Initial connection to AmazonWebServices made.
   2016-07-29 16:53:42,772 - aws_ir.cli - INFO - Inventory AWS Regions Complete 11 found.
   2016-07-29 16:53:42,772 - aws_ir.cli - INFO - Inventory Availability Zones Complete 27 found.
   2016-07-29 16:53:42,773 - aws_ir.cli - INFO - Beginning inventory of instances world wide.  This might take a minute...
   2016-07-29 16:53:49,527 - aws_ir.cli - INFO - Inventory complete.  Proceeding to resource identification.
   2016-07-29 16:53:54,839 - aws_ir.cli - INFO - Set satus of access key AKIAJGOVL2FIYOG6YFIA to Inactive
   Processing complete

Host Compromise
***************

The ``aws_ir`` subcommand ``host-compromise`` preserves forensic artifacts from a compromised host after isolating the host.
Once all artifacts are collected and tagged the compromised instance is powered off.
The ``host-compromise`` subcommand takes three arguments, the ``instance-ip`` of the compromised host, a ``user`` with ssh access to the target instance, and the ``ssh-key`` used for authentication.

.. note:: Currently ``user`` must be capable of passwordless sudo for memory capture to complete.  If ``user`` does not have passwordless sudo capabilities all artifiacts save for the memory capture will be gathered.

.. code-block:: bash

   $ aws_ir host_compromise -h
   usage: aws_ir host-compromise [-h] --instance-ip INSTANCE_IP --user USER
                                 --ssh-key SSH_KEY
   
   optional arguments:
     -h, --help            show this help message and exit
     --instance-ip INSTANCE_IP
     --user USER           this is the privileged ssh user for acquiring memory
                           from the instance.
     --ssh-key SSH_KEY     provide the path to the ssh private key for the user.

.. note:: AWS IR saves all forensic artifacts except for disk snapshots in an s3 bucket created for each case.  Disk snapshots are tagged with the same case number as the rest of the rest of the artifacts.

Below is the output of running the ``host-compromise`` subcommand.

.. code-block:: bash

   $ aws_ir host_compromise --instance-ip 52.42.254.41 --user ec2-user --ssh-key key.pem
   2016-07-28 16:02:17,104 - aws_ir.cli - INFO - Initial connection to AmazonWebServices made.
   2016-07-28 16:02:23,741 - aws_ir.cli - INFO - Inventory AWS Regions Complete 11 found.
   2016-07-28 16:02:23,742 - aws_ir.cli - INFO - Inventory Availability Zones Complete 27 found.
   2016-07-28 16:02:23,742 - aws_ir.cli - INFO - Beginning inventory of instances world wide.  This might take a minute...
   2016-07-28 16:02:30,398 - aws_ir.cli - INFO - Inventory complete.  Proceeding to resource identification.
   2016-07-28 16:02:35,608 - aws_ir.cli - INFO - Security Group Created sg-a25e0fc4
   2016-07-28 16:02:35,895 - aws_ir.cli - INFO - Security Group Egress Access Revoked for sg-a25e0fc4
   2016-07-28 16:02:36,206 - aws_ir.cli - INFO - Access Ingress Added for proto=tcp from=22 to=22 cidr_range=0.0.0.0/0 for sg=sg-a25e0fc4
   2016-07-28 16:02:36,475 - aws_ir.cli - INFO - Shifted instance into isolate security group.
   2016-07-28 16:02:37,975 - aws_ir.cli - INFO - Took a snapshot of volume vol-68accce1 to snapshot snap-d5c4e32f
   2016-07-28 16:02:38,078 - aws_ir.cli - INFO - Attempting run margarita shotgun for ec2-user on 52.42.254.41 with key.pem
   2016-07-28 16:02:38,592 margaritashotgun.repository [INFO] downloading https://threatresponse-lime-modules.s3.amazonaws.com/lime-4.4.11-23.53.amzn1.x86_64.ko as lime-2016-07-28T16:02:38.591954-4.4.11-23.53.amzn1.x86_64.ko
   2016-07-28 16:02:39,817 margaritashotgun.memory [INFO] 52.42.254.41: dumping memory to s3://cloud-response-38c5c23e79e24bc8a5d5d79103b312ff/52.42.254.41-mem.lime
   2016-07-28 16:03:06,466 margaritashotgun.memory [INFO] 52.42.254.41: capture 10% complete
   2016-07-28 16:03:20,368 margaritashotgun.memory [INFO] 52.42.254.41: capture 20% complete
   2016-07-28 16:03:35,419 margaritashotgun.memory [INFO] 52.42.254.41: capture 30% complete
   2016-07-28 16:03:49,523 margaritashotgun.memory [INFO] 52.42.254.41: capture 40% complete
   2016-07-28 16:04:03,385 margaritashotgun.memory [INFO] 52.42.254.41: capture 50% complete
   2016-07-28 16:04:18,561 margaritashotgun.memory [INFO] 52.42.254.41: capture 60% complete
   2016-07-28 16:04:32,104 margaritashotgun.memory [INFO] 52.42.254.41: capture 70% complete
   2016-07-28 16:04:45,952 margaritashotgun.memory [INFO] 52.42.254.41: capture 80% complete
   2016-07-28 16:05:05,152 margaritashotgun.memory [INFO] 52.42.254.41: capture 90% complete
   2016-07-28 16:05:18,778 margaritashotgun.memory [INFO] 52.42.254.41: capture complete: s3://cloud-response-38c5c23e79e24bc8a5d5d79103b312ff/52.42.254.41-mem.lime
   2016-07-28 16:05:19,306 - aws_ir.cli - INFO - memory capture completed for: ['52.42.254.41'], failed for: []
   2016-07-28 16:05:19,454 - aws_ir.cli - INFO - Stopping instance: instance_id=i-ef048f40
   Processing complete


User Guide
**********

Read more about each subcommand in our `user guide <https://aws_ir.readthedocs.io/en/latest/user_guide.html>`__.
