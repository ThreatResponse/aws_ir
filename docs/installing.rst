
Installation
============

System Requirements
*******************

Currently only linux is a supported platform.  Python 3 compatability is maintained where possible but the tip of the master branch may only function in a Python 2 environment.

While aws_ir is written purely in python, some of the libraries used require additional system packages.

Fedora / REHL Distributions
---------------------------

* python-devel (Python 2.7+)
* python-pip
* libffi-devel
* libssl-devel

Debian Distributions
--------------------

* python-dev (Python 2.7+)
* python-pip
* libffi-dev
* libssl-dev

Installing from PyPi
********************

AWS_IR is not currently listed in PyPi, while we work on that install via one of the methods below.


Installing From Github
**********************

.. code-block:: bash

   $ pip install git+ssh://git@github.com/ThreatResponse/aws_ir.git@master
   $ margaritashotgun -h

Local Build and Install
***********************

.. code-block:: bash

   $ git clone https://github.com/ThreatResponse/aws_ir.git
   $ cd aws_ir
   $ python setup.py
   $ pip install dist/aws_ir-*.tar.gz
   $ margaritashotgun -h

Local Execution
***************

In the previous two example dependencies are automatically resolved, if you simply want to run aws_ir using the script ``bin/aws_ir`` you will have to manually install dependencies

.. code-block:: bash

   $ git clone https://github.com/ThreatResponse/aws_ir.git
   $ cd aws_ir
   $ pip install -r requirements.txt
   $ ./bin/aws_ir -h

