
Installation
============

System Requirements
*******************

ThreatResponse requires python >= 3.4.


Installing from PyPi
********************

.. code-block:: bash
   $ python3 -m virtualenv env
   $ source/env/bin/activate
   $ pip install aws_ir
   $ aws_ir -h


Installing From Github
**********************

.. code-block:: bash

   $ python3 -m virtualenv env
   $ source/env/bin/activate
   $ pip install git+ssh://git@github.com/ThreatResponse/aws_ir.git@master
   $ aws_ir -h

Local Build and Install
***********************

.. code-block:: bash

   $ git clone https://github.com/ThreatResponse/aws_ir.git
   $ cd aws_ir
   $ python3 -m virtualenv env
   $ source/env/bin/activate
   $ pip install .
   $ aws_ir -h

Local Execution
***************

In the previous two example dependencies are automatically resolved, if you simply want to run aws_ir using the script ``bin/aws_ir`` you will have to manually install dependencies

.. code-block:: bash

   $ git clone https://github.com/ThreatResponse/aws_ir.git
   $ cd aws_ir
   $ python3 -m virtualenv env
   $ source/env/bin/activate
   $ pip install -r requirements.txt
   $ ./bin/aws_ir -h

Using Docker
************

.. code-block:: bash

   $ git clone https://github.com/ThreatResponse/aws_ir.git
   $ cd aws_ir
   $ docker-compose build aws_ir
   $ docker-compose run aws_ir bash
   $ pip install .


AWS Credentials Using MFA and AssumeRole
*****************************************

Many users of aws_ir have requested the ability to use the tooling with mfa and
assumeRole functionality.  While we don't natively support this yet v0.3.0 sets
the stage to do this natively by switching to boto-session instead of thick clients.

For now if you need to use the tool with MFA we recommend:

`https://pypi.python.org/pypi/awsmfa/0.2.4 <https://pypi.python.org/pypi/awsmfa/0.2.4>`_.

.. code-block:: bash

    aws-mfa \
    --device arn:aws:iam::12345678:mfa/bobert \
    -assume-role arn:aws:iam::12345678:role/ResponderRole \
    --role-session-name \"bobert-ir-session\"

awsmfa takes a set of long lived access keys from a boto profile called [default-long-lived]
and uses those to generate temporary session tokens that are automatically put into
the default boto profile.  This ensures that any native tooling that doesn't support
MFA + AssumeRole can still leverage MFA and short lived credentials for access.


Some Linux distributions require additional system packages
***********************************************************

Fedora / RHEL Distributions
---------------------------

* python-devel (Python 3.4+)
* python-pip
* libffi-devel
* libssl-devel

Debian Distributions
--------------------

* python-dev (Python 3.4+)
* python-pip
* libffi-dev
* libssl-dev
