__version__ = '0.2.1'

import logging


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
    logging.setLoggerClass(TimesketchLogger)
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

    def _log(self, level, msg, args, exc_info=None, extra=None):
        if extra is None:
            extra = self.__get_times()
        super(TimesketchLogger, self)._log(level, msg, args, exc_info, extra)

    def __get_times(self):
        tm = int(time.time())
        dt = datetime.utcfromtimestamp(tm).isoformat()
        times = {'unixtime': tm, 'isotime': dt}
        return times


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logging.getLogger('margaritashotgun').addHandler(NullHandler())
