import logging
import os
import sys


class Logger():
    def __init__(self, logLevel):
        self.logger = logging.getLogger(__name__)
        self.setLevel(logLevel)

        # Add logging handler to print the log statement to standard output device
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # https://stackoverflow.com/questions/533048/how-to-log-source-file-name-and-line-number-in-python
        # https://docs.python.org/3/library/logging.html#logrecord-attributes

        # Simplify log output for Production
        if os.getenv('CDX_APP_ENV') == 'production':
            formatter = logging.Formatter('%(levelname)-s - %(filename)s - Line:%(lineno)d - %(message)s - %(context)s', '%Y-%m-%d %H:%M:%S')

        else:
            formatter = logging.Formatter(
                '[%(asctime)s.%(msecs)03d] %(levelname)-s - %(filename)s - {%(funcName)s:%(lineno)d} - %(message)s - %(context)s',
                '%Y-%m-%d %H:%M:%S',
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def setLevel(self, logLevel):
        self.logger.setLevel(logLevel)

    def debug(self, msg, *args, extra=None, **kwargs):
        """
        Log 'msg % args' with severity 'DEBUG'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.debug(msg, *args, extra={"context": {}}, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.debug(msg, *args, extra=extra, **kwargs)

    def info(self, msg, *args, extra=None, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.info(msg, *args, extra={"context": {}}, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.info(msg, *args, extra=extra, **kwargs)

    def warning(self, msg, *args, extra=None, **kwargs):
        """
        Log 'msg % args' with severity 'WARNING'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.warning(msg, *args, extra={"context": {}}, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.warning(msg, *args, extra=extra, **kwargs)

    def error(self, msg, *args, extra=None, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.error(msg, *args, extra={"context": {}}, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.error(msg, *args, extra=extra, **kwargs)

    def exception(self, msg, *args, extra=None, exc_info=True, **kwargs):
        """
        Log 'msg % args' with severity 'EXCEPTION'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.exception(msg, *args, extra={'context': {}}, exc_info=exc_info, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.exception(msg, *args, extra=extra, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, extra=None, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass additional context, use keyword argument extra with
        a json value, e.g.

        """
        if extra is None:
            self.logger.critical(msg, *args, extra={"context": {}}, **kwargs)

        else:
            extra = {'context': extra}
            self.logger.critical(msg, *args, extra=extra, **kwargs)


log_client = None


def get_logger(logLevel):
    global log_client

    """Call this method just once. To create a new logger."""
    log_client = Logger(logLevel) if not log_client else log_client

    return log_client
