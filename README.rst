AWS IR
======

Python installable command line utility for mitigation of host and key compromises.

Documentation
-------------

Read the full documentation on `read the docs <https://aws_ir.readthedocs.io/en/latest/>`__.

Quickstart
----------

For more information see the `user guide <https://aws_ir.readthedocs.io/en/latest/user_guide.html>`__.

Installation
************

``pip install git+ssh://git@github.com/ThreatResponse/aws_ir.git@master``

Or see `installing <https://aws_ir.readthedocs.io/en/latest/installing.html>`__.

AWS Credentials
***************

Ensure aws credentials are configured under the user running aws_ir as documented `by amazon <https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`__.

Check back soon for an IAM policy featuring the minimum set of required permissions

Key Compromise
**************

The ``aws_ir`` subcommand ``key_compromise`` disables access keys in the case of a key compromise.
It's arguments are the access key id and region in which the key was provisioned.
The compromised access key is disabled via the AWS api.

.. code-block:: bash

   $ aws_ir key_compromise -h
   usage: aws_ir key_compromise [-h] compromised_access_key_id region

Below is the output of running the ``key_compromise`` subcommand.

.. code-block:: bash

   $ aws_ir key_compromise AKIAJGOVL2FIYOG6YFIA us-west-2
   2016-07-29 16:53:35,458 - aws_ir.cli - INFO - Initial connection to AmazonWebServices made.
   2016-07-29 16:53:42,772 - aws_ir.cli - INFO - Inventory AWS Regions Complete 11 found.
   2016-07-29 16:53:42,772 - aws_ir.cli - INFO - Inventory Availability Zones Complete 27 found.
   2016-07-29 16:53:42,773 - aws_ir.cli - INFO - Beginning inventory of instances world wide.  This might take a minute...
   2016-07-29 16:53:49,527 - aws_ir.cli - INFO - Inventory complete.  Proceeding to resource identification.
   2016-07-29 16:53:54,839 - aws_ir.cli - INFO - Set satus of access key AKIAJGOVL2FIYOG6YFIA to Inactive
   Processing complete : Launch an analysis workstation with the command
   
                    aws_ir -n cr-16-072916-46a8 create_workstation us-west-2

Host Compromise
***************

The ``aws_ir`` subcommand ``host_compromise`` preserves forensic artifacts from a compromised host after isolating the host.
Once all artifacts are collected and tagged the compromised instance is powered off.
The ``host_compromise`` subcommand takes three arguments, the ``ip`` of the compromised host, a ``user`` with ssh access to the target instance, and the ``ssh_key_file`` used for authentication.

Currently ``user`` must be capable of passwordless sudo for memory capture to complete.  If ``user`` does not have passwordless sudo capabilities all artifiacts save for the memory capture will be gathered.

.. code-block:: bash

   $ aws_ir host_compromise -h
   usage: aws_ir host_compromise [-h] ip user ssh_key_file

AWS IR saves all forensic artifacts except for disk snapshots in an s3 bucket created for each case.  Disk snapshots are tagged with the same case number as the rest of the rest of the artifacts.

Below is the output of running the ``host_compromise`` subcommand.

.. code-block:: bash

   $ aws_ir host_compromise 52.42.254.41 ec2-user key.pem
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
   Processing complete : Launch an analysis workstation with the command 
   
                   aws_ir -n cr-16-072816-a4d6 create_workstation us-west-2

Launch Analysis Workstation
***************************

Once either the ``key_compromise`` or the ``host_compromise`` subcommands have been run an incident response workstation can be launched using the ``create_workstation`` subcommand.
The ``create_workstation`` subcommand launches an incident response workstation running `Threat Response Web <https://github.com/ThreatResponse/threatresponse_web>`__.
The full power of ``aws_ir`` is availible from the workstation, as well as additional insights about your AWS account.
From the workstation additional hosts and keys can be processed, for more information about the post-processing completed by the workstation see the `Threat Response Web documentation <https://github.com/ThreatResponse/threatresponse_web>`__.

To launch a workstation provide ``aws_ir`` with the case number generated from an earlier run and specify the region in which the workstation will be launched.


.. code-block:: bash

   $ aws_ir -n cr-16-072816-a4d6 create_workstation us-west-2
   2016-07-28 16:23:09,813 - aws_ir.cli - INFO - Wrote new key to /tmp/cr-16-072816-a4d6HHjGB4.pem
   2016-07-28 16:23:10,205 - aws_ir.cli - INFO - Found policy: cloudresponse_workstation-cr-16-072816-a4d6-us-west-2
   2016-07-28 16:23:10,379 - aws_ir.cli - INFO - Created new security vpc vpc-afca9dcb
   2016-07-28 16:23:10,614 - aws_ir.cli - INFO - Created new security group sg-184b1a7e
   2016-07-28 16:23:10,986 - aws_ir.cli - INFO - Access Ingress Added for proto=tcp from=22 to=22 cidr_range=0.0.0.0/0 for sg=sg-184b1a7e
   2016-07-28 16:23:11,137 - aws_ir.cli - INFO - Created new subnet with id subnet-271ec47f
   2016-07-28 16:23:11,238 - aws_ir.cli - INFO - Created InternetGateway with ID igw-db6d95bf
   2016-07-28 16:23:11,282 - aws_ir.cli - INFO - Attaching InternetGateway igw-db6d95bf to VPC vpc-afca9dcb
   2016-07-28 16:23:11,282 - aws_ir.cli - INFO - Checking if InternetGateway igw-db6d95bf is attached to VPC vpc-afca9dcb
   2016-07-28 16:23:12,218 - aws_ir.cli - INFO - Launching AMI ami-4c07c52c to instace id i-f70b612a
   2016-07-28 16:23:13,505 - aws_ir.cli - INFO - Checking if instance i-f70b612a is running.
   2016-07-28 16:23:14,578 - aws_ir.cli - INFO - Checking if instance i-f70b612a is running.
   2016-07-28 16:23:15,637 - aws_ir.cli - INFO - Checking if instance i-f70b612a is running.
   2016-07-28 16:23:16,689 - aws_ir.cli - INFO - Checking if instance i-f70b612a is running.
   2016-07-28 16:23:35,863 - aws_ir.cli - INFO - Instance i-f70b612a is running at 52.43.1.39
   2016-07-28 16:23:35,865 - aws_ir.cli - INFO - connect to the workstation instance with: ssh -i /tmp/cr-16-072816-a4d6HHjGB4.pem -L9999:127.0.0.1:9999 -L5000:127.0.0.1:5000 -L3000:127.0.0.1:3000 ec2-user@52.43.1.39
   connect to the workstation instance with:
    ssh -i /tmp/cr-16-072816-a4d6HHjGB4.pem -L9999:127.0.0.1:9999 -L5000:127.0.0.1:5000 -L3000:127.0.0.1:3000 ec2-user@52.43.1.39

After the ``create_workstation`` command completes use the provided ssh command to mount the workstation's webapps to your local system.

User Guide
**********

Read more about each subcommand in our `user guide <https://aws_ir.readthedocs.io/en/latest/user_guide.html>`__.
