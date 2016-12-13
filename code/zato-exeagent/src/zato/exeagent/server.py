# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import logging
from traceback import format_exc

# Bunch
from bunch import Bunch

# gevent
from gevent.pywsgi import WSGIServer

# ################################################################################################################################

logger = logging.getLogger(__name__)

# ################################################################################################################################

ok = b'200 OK'
headers = [(b'Content-Type', b'application/json')]

# ################################################################################################################################

class Config(object):
    """ Encapsulates configuration of various agent-related layers.
    """
    def __init__(self):
        self.main = Bunch()

# ################################################################################################################################

class ExeAgentServer(object):
    """ Main class spawning .exe commands and listening for API requests.
    """
    def __init__(self, config, repo_location):
        self.config = config
        self.repo_location = repo_location

        main = self.config.main

        if main.crypto.use_tls:
            priv_key, cert = main.crypto.priv_key_location, main.crypto.cert_location
        else:
            priv_key, cert = None, None

        # API server
        self.api_server = WSGIServer((main.bind.host, int(main.bind.port)), self, keyfile=priv_key, certfile=cert)

# ################################################################################################################################

    def serve_forever(self):
        self.api_server.serve_forever()

# ################################################################################################################################

    def __call__(self, env, start_response):
        try:
            start_response(ok, headers)
            return [b'{}\n']
        except Exception as e:
            logger.warn(format_exc(e))

# ################################################################################################################################
