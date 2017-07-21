
Installation
============

System Requirements
*******************

ThreatResponse now requires python >= 3.4.  It may still work(ish) with Python 2.7 but is not recommended due
to security problems with cryptography libraries in Python 2.7.

While aws_ir is written purely in python, some of the libraries used require additional system packages.

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

Installing from PyPi
********************

.. code-block:: bash

   $ pip install aws_ir


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

