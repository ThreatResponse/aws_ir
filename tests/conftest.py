from localstack.mock import infra


def pytest_sessionstart(session):
    """ before session.main() is called. """
    infra.start_infra(async=True)
    pass


def pytest_sessionfinish(session, exitstatus):
    """ whole test run finishes. """
    infra.stop_infra()
    pass
