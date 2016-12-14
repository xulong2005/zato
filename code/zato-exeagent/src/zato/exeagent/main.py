# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# First thing in the process
from gevent import monkey
monkey.patch_all()

# stdlib
import logging
import os
from logging.config import dictConfig
from platform import uname
from traceback import format_exc

# appdirs
from appdirs import user_config_dir, user_log_dir

# ConcurrentLogHandler - updates stlidb's logging config on import so this needs to stay
import cloghandler
cloghandler = cloghandler # For pyflakes

# YAML
import yaml

# Zato
from zato.exeagent.default import exeagent_conf, logging_conf
from zato.exeagent.server import Config, ExeAgentServer
from zato.exeagent.util import absjoin, get_config, store_pidfile

# ################################################################################################################################

app_name = 'ExeAgent' if 'windows' in uname().system.lower() else 'exeagent'
app_author = 'Zato Source s.r.o.'
app_version = '1'

# ################################################################################################################################

class CONF:
    EXEAGENT = 'exeagent.conf'
    LOGGING = 'logging.conf'

# ################################################################################################################################

def _set_up_config():
    pass

# ################################################################################################################################

def get_config_file_location(conf):
    pass

# ################################################################################################################################

def main():

    # Always attempt to store the PID file first
    store_pidfile(os.path.abspath('.'))

    # Capture warnings to log files
    logging.captureWarnings(True)

    config = Config()

    print(user_config_dir(app_name, app_author))
    print(user_log_dir(app_name, app_author))

    return

    repo_location = os.path.join('.', 'config', 'repo')

    # Logging configuration
    with open(os.path.join(repo_location, 'logging.conf')) as f:
        dictConfig(yaml.load(f))

    # Read config in and make paths absolute
    config.main = get_config(repo_location, 'exeagent.conf')

    if config.main.crypto.use_tls:
        config.main.crypto.ca_certs_location = absjoin(repo_location, config.main.crypto.ca_certs_location)
        config.main.crypto.priv_key_location = absjoin(repo_location, config.main.crypto.priv_key_location)
        config.main.crypto.cert_location = absjoin(repo_location, config.main.crypto.cert_location)

    logger = logging.getLogger(__name__)
    logger.info('Scheduler starting (http{}://{}:{})'.format(
        's' if config.main.crypto.use_tls else '', config.main.bind.host, config.main.bind.port))

    # Fix up configuration so it uses the format internal utilities expect
    for name, job_config in get_config(repo_location, 'startup_jobs.conf', needs_user_config=False).items():
        job_config['name'] = name
        config.startup_jobs.append(job_config)

    # Run the scheduler server
    try:
        ExeAgentServer(config, repo_location).serve_forever()
    except Exception as e:
        logger.warn(format_exc(e))

if __name__ == '__main__':
    main()

# ################################################################################################################################
