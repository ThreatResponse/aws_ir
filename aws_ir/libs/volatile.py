import logging
import margaritashotgun
import platform

from margaritashotgun.repository import Repository

logger = logging.getLogger(__name__)


class Memory(object):
    def __init__(
        self,
        compromised_resource,
        dry_run,
        boto_session
    ):

        self.session = boto_session
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
        config = dict(
            aws=dict(bucket=bucket),
            hosts=[
                dict(
                    addr=ip, port=port,
                    username=user,
                    password=password,
                    key=key
                )
            ],
            workers='auto',
            logging={
                    'dir': '/tmp/',
                    'prefix': ("{case_number}-{ip}").format(
                        ip=ip,
                        case_number=case_number
                    )
            },
            repository=dict(
                enabled=True,
                url=('https://threatresponse-lime'
                     '-modules.s3.amazonaws.com/')
            )
        )
        if 'Darwin' in platform.system():
            config['repository']['gpg_verify'] = False
        capture_client = margaritashotgun.client(
            name=name,
            config=config,
            library=True,
            verbose=self.verbose
        )

        try:
            repository_url = 'https://threatresponse-lime-modules.s3.amazonaws.com/'
            if 'Darwin' in platform.system():
                repository_gpg_verify = False
            else:
                repository_gpg_verify = True

            self.repo = Repository(repository_url, repository_gpg_verify)

            if 'Darwin' not in platform.system():
                self.repo.init_gpg()

            return capture_client.run()
        except Exception:
            if 'Darwin' not in platform.system():
                logger.critical("GPG key not in trust chain attempting interactive installation.")
                self.repo.prompt_for_install()
            return capture_client.run()
