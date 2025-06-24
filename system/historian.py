import logging
import logging.handlers
import colorlog

from typing import List
from datetime import datetime
from system.configuration import Configuration


class Logging:
    loggers: List[logging.Logger]

    def __init__(self, conf: Configuration):
        self.loggers = []

        for conf_logger in conf.loggers:
            print(conf_logger)
            logger = logging.Logger(conf_logger['name'])
            formatter: logging.Formatter
            handler: logging.Handler

            if conf_logger['file']:
                now = datetime.now().strftime('%d-%m-%Y_%H%M%S')
                name = str(conf_logger['file']).replace('[datetime]', now)
                handler = logging.handlers.TimedRotatingFileHandler(
                    filename=name,
                    encoding='utf-8',
                    when='midnight'
                )
                handler.setLevel(conf_logger['level'])
                formatter = logging.Formatter(conf_logger['format'], '%Y-%m-%d %H:%M:%S', style='{')
            else:
                handler = colorlog.StreamHandler()
                handler.setLevel(conf_logger['level'])
                formatter = colorlog.ColoredFormatter(
                    conf_logger['format'],
                    '%Y-%m-%d %H:%M:%S',
                    reset=True,
                    log_colors={
                        'DEBUG': 'bold_light_white',
                        'INFO': 'bold_cyan',
                        'WARNING': 'bold_yellow',
                        'ERROR': 'bold_red',
                        'CRITICAL': 'bold_red,bg_white'
                    },
                    style='{'
                )

            handler.setFormatter(formatter)

            logger.addHandler(handler)
            self.loggers.append(logger)

    def debug(self, message):
        for logger in self.loggers:
            logger.debug(message)

    def info(self, message):
        for logger in self.loggers:
            logger.info(message)

    def warning(self, message):
        for logger in self.loggers:
            logger.warn(message)

    def error(self, message):
        for logger in self.loggers:
            logger.error(message)

    def critical(self, message):
        for logger in self.loggers:
            logger.critical(message)
