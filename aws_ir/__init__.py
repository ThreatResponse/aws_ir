__version__ = '0.2.1'

import logging
import time
from datetime import datetime


def set_stream_logger(name="aws_ir", level=logging.INFO,
                      format_string=None):
    """
    """

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    time_format = "%Y-%m-%dT%H:%M:%S"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(level)
    streamFormatter = logging.Formatter(format_string, time_format)
    streamHandler.setFormatter(streamFormatter)
    logger.addHandler(streamHandler)


def set_file_logger(case_number, name="aws_ir", level=logging.INFO,
                    base_dir="/tmp", desc="AWS_IR Action"):
    """
    """

    log_file = "{base_dir}/{case_number}-aws_ir.log".format(
                   base_dir=base_dir, case_number=case_number
               )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setLevel(level)
    fileFormatter = logging.Formatter(
        "\t{'timestamp': %(unixtime)s, 'message': '%(message)s', " +
        "desc: '{desc}', 'datetime': '%(isotime)s'}},".format(desc=desc)
    )
    fileHandler.setFormatter(fileFormatter)
    logger.addHandler(fileHandler)


class TimesketchLogger(logging.getLoggerClass()):

    def __init__(self, *args, **kwargs):
        super(TimesketchLogger, self).__init__(*args, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None):
        super(TimesketchLogger, self)._log(level, msg, args, exc_info=exc_info,
                                           extra=self.__get_times())
    def __get_times(self):
        tm = int(time.time())
        dt = datetime.utcfromtimestamp(tm).isoformat()
        times = {'unixtime': tm, 'isotime': dt}
        return times


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logging.setLoggerClass(TimesketchLogger)
logging.getLogger('aws_ir').addHandler(NullHandler())
