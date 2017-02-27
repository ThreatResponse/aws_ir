__version__ = '0.2.2'

import os
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

def wrap_log_file(case_number, base_dir="/tmp"):
    """
    """
    log_file = "{base_dir}/{case_number}-aws_ir.log".format(
                   base_dir=base_dir, case_number=case_number
               )
    # if log_file exists and is not empty  append a closing "]" to the file
    if os.path.isfile(log_file) and (os.path.getsize(log_file) > 0):
        with open(log_file, 'a') as f:
            f.write("]")
            f.flush()
            f.close()
    # otherwise write an opening "[" to the file
    else:
        with open(log_file, 'w+') as f:
            f.write("[\n")
            f.flush()
            f.close()

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
