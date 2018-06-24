import os
import aws_ir
from aws_ir import TimesketchLogger
import logging

CASE_NUMBER = "cr-17-000001-2d2d"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = "{0}/{1}-aws_ir.log".format(BASE_DIR, CASE_NUMBER)


class TestLogging(object):

    def test_logging(self):
        logger = logging.getLogger('aws_ir')

        # ensure custom logger class is in place
        assert logger.__class__ == TimesketchLogger

        # ensure that null log handler is in place by default
        assert len(logger.handlers) == 1
        assert logger.handlers[0].__class__ == aws_ir.NullHandler

        # setup stream handler and ensure the object was created
        aws_ir.set_stream_logger(level=logging.INFO)
        assert len(logger.handlers) == 2
        assert logger.handlers[1].__class__ == logging.StreamHandler

        # setup file handler and ensure the object was created
        aws_ir.set_file_logger(
            CASE_NUMBER, base_dir=BASE_DIR,
            level=logging.INFO
        )
        assert len(logger.handlers) == 3
        assert logger.handlers[2].__class__ == logging.FileHandler

        # test log file is created
        aws_ir.wrap_log_file(CASE_NUMBER, base_dir=BASE_DIR)
        logger.info("test of file log")
        assert os.path.isfile(LOG_FILE) is True
        aws_ir.wrap_log_file(CASE_NUMBER, base_dir=BASE_DIR)

        # check file contents
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            assert "[" in lines[0]
            assert "test of file log" in lines[1]
            assert "]" in lines[-1]

    def teardown_method(self, method):
        # clear all but the aws_ir.NullHandler
        logger = logging.getLogger('aws_ir')
        for handler in logger.handlers:
            if handler.__class__ != aws_ir.NullHandler:
                logger.removeHandler(handler)

        # cleanup the log file if it was created
        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)
