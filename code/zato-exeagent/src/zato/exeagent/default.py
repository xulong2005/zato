# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

exeagent_conf = """
"""

logging_conf = """
loggers:
    '':
        level: INFO
        handlers: [stdout, default]
    zato:
        level: INFO
        handlers: [stdout, default]
        qualname: zato
        propagate: false
handlers:
    default:
        formatter: default
        class: logging.handlers.ConcurrentRotatingFileHandler
        filename: 'exeagent.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
formatters:
    default:
        format: '%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s'
version: 1
"""
