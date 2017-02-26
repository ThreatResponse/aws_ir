import logging
import margaritashotgun

logger = logging.getLogger(__name__)


class Memory(object):
    def __init__(
        self,
        compromised_resource,
        dry_run,
        client=None
    ):

        self.client = client
        self.compromised_resource = compromised_resource
        self.compromise_type = compromised_resource['compromise_type']
        self.dry_run = dry_run
        # Check if logging level is set to logging.DEBUG
        if logger.getEffectiveLevel() < logging.INFO:
            self.verbose = True
        else:
            self.verbose = False

    def get_memory(
        self,
        bucket,
        ip,
        user,
        key,
        case_number,
        port=None,
        password=None
    ):
        name = 'margaritashotgun'
        config = dict(aws = dict(bucket = bucket),
                      hosts = [ dict(addr = ip, port = port,
                                    username = user,
                                    password = password,
                                    key = key) ],
                      workers = 'auto',
                      logging = { 'dir': '/tmp/',
                                  'prefix':  ("{case_number}-{ip}").format(
                                                ip=ip,
                                                case_number=case_number ) },
                      repository = dict(enabled = True,
                                        url = ('https://threatresponse-lime'
                                               '-modules.s3.amazonaws.com/')))
        capture_client = margaritashotgun.client(name=name, config=config,
                                                 library=True, verbose=self.verbose)
        return capture_client.run()
