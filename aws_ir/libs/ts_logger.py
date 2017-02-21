import time
import pytz
import sys
import logging
import structlog
import json
import os
from structlog import get_logger, configure
from structlog import wrap_logger
from structlog import ReturnLogger
from structlog import PrintLogger
from structlog.stdlib import filter_by_level
from structlog.processors import JSONRenderer
from datetime import datetime

class timesketch_logger(object):
    def __init__(self, message, case_number):
        #Logging setup for json only
        self.message = message
        self.timestamp = int(time.time())
        self.datetime = datetime.utcnow().isoformat()
        self.desc = "AWS_IR Action"


        configure(
            processors=[JSONRenderer(indent=1, sort_keys=True)],
            context_class=structlog.threadlocal.wrap_dict(dict),
            logger_factory=structlog.stdlib.LoggerFactory()
        )

        self.log = get_logger('aws_ir.json')

        event = ReturnLogger().msg(
            'message',
            message=self.message,
            timestamp=self.timestamp,
            datetime=self.datetime,
            desc=self.desc
        )


        def generate_log_filename(case_number):
            filename = ("/tmp/{case_number}-aws_ir.log").format(case_number=case_number)
            return filename

        def log_file_exists():
            exists = os.path.isfile(self.logfile)
            return exists

        self.logfile = generate_log_filename(case_number)

        def file_len(fname):
           i = 0
           with open(fname) as f:
               for i, l in enumerate(f):
                   pass
           return i + 1

        def log_file_contains_events(logfile):
            length = file_len(logfile)
            if length >= 2:
                return True
            else:
                return False

    def stub_ts_file(logfile):
            with open(logfile, "w") as f:
                f.write("[ \n")
            f.close()

    def write_log_event(event):
        logfile = self.logfile
        if log_file_exists():
            if (log_file_contains_events(logfile) == True):
                f = open(logfile)
                lines = f.readlines()
                f.close()
                with open(logfile,'w') as w:
                    w.writelines([item for item in lines[:-1]])
                    w.write("\t" + str(event) + ",")
                    w.write("\n")
                    w.write("]")
                    w.close()
            else:
               stub_ts_file(logfile)
               with open(logfile,'a') as w:
                   w.write("\t" + str(event) + ",")
                   w.write("\n")
                   w.write("]")
                   w.close()
        else:
            stub_ts_file(logfile)
            with open(logfile,'a') as w:
               w.write("\t" + str(event) + ",")
               w.write("\n")
               w.write("]")
               w.close()
        write_log_event(event[1])
