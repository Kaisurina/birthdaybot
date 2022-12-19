import logging
import re


class CustomFormatter(logging.Formatter):
    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt: str | None = ...) -> None:
        super().__init__(fmt)
        self.FORMATS = {
            logging.DEBUG: self.grey + self._fmt + self.reset,
            logging.INFO: self.blue + self._fmt + self.reset,
            logging.WARNING: self.yellow + self._fmt + self.reset,
            logging.ERROR: self.red + self._fmt + self.reset,
            logging.CRITICAL: self.bold_red + self._fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        colorized = logging.Formatter(log_fmt)
        return colorized.format(record)


class FileCustomFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        try:
            return re.sub(fr"{record.message}", re.sub(r"([\n\t\f\r\b\\\"])", r"\\\1", record.message), result)
        except:
            return result
