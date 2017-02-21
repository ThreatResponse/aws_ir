aws_ir Plugin Support ( Experimental )
=======================================

All plugins need to take the following:
  * Client : A boto3 client object with a connection to appropriate region
  * Compromised Resource: A dictionary of information gathered during inventory this also includes case_number and compromise type in the dictionary.
  * Dry Run Flag : True / False will eventually propogate from dry_run flag upstream.
