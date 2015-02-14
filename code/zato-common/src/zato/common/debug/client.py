# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
import socket
from cmd import Cmd
from datetime import datetime, timedelta
from json import dumps, loads
from thread import start_new_thread
from traceback import format_exc

# gevent
import gevent

# Zato
from zato.common.debug import Connection as _Connection, Message, MESSAGE_TYPE
from zato.common.util import new_cid

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# ################################################################################################################################

class Connection(_Connection):
    def __init__(self, host='localhost', port=19055, buff_size=8192, connect_timeout=4, sleep_time=0.2):
        super(Connection, self).__init__(socket.socket(socket.AF_INET, socket.SOCK_STREAM), (host, port))
        self.buff_size = buff_size
        self.connect_timeout = connect_timeout
        self.sleep_time = sleep_time
        self.is_connected = False
        self.keep_running = True
        self.session_id = None
        self.sock_file = self.socket.makefile()

# ################################################################################################################################

    def connect(self):
        """ Connect to the server or time out and raise an exception.
        """
        start = now = datetime.utcnow()
        until = start + timedelta(seconds=self.connect_timeout)

        while not self.is_connected:

            if now >= until:
                raise ConnectionException('Could not connect to `{}` after `{}`s.'.format(self.address, self.connect_timeout))

            try:
                self.socket.connect(self.address)
            except socket.error, e:
                logger.debug('Could not connect to `%s`, e:`%s`', self.address, format_exc(e))
                gevent.sleep(self.sleep_time)
                now += timedelta(seconds=self.sleep_time)
            else:
                self.is_connected = True

        msg = 'Connected to `%s`'

        took = now-start
        if took:
            msg += ' after `{}`'.format(took)

        logger.info(msg, self.address)

# ################################################################################################################################

    def handle_welcome_req(self, msg):
        self.session_id = msg.session_id
        self.send_response(msg)

# ################################################################################################################################

    def send(self, msg):
        self.sock_file.write(msg.to_wire())
        self.sock_file.flush()

# ################################################################################################################################

    def run_forever(self):
        """ Establish a connection and keep running until told to stop.
        """
        # Will raise an exception if it doesn't succeed
        self.connect()

        # Blocks for as long as the client is connected
        self.main_loop()

# ################################################################################################################################

class Client(object):
    """ A base class for debugging clients - encapsulates logic common to all
    subclasses, regardless of whether they implement console or web-based access.
    """
    def __init__(self):
        self.connection = Connection()
        self.session_id = None
        self.req_to_server = {}
        self.resp_from_server = {}

# ################################################################################################################################

    def run_forever(self):
        start_new_thread(self.connection.run_forever, ())

# ################################################################################################################################

class ConsoleClient(Client):
    pass

# ################################################################################################################################

if __name__ == '__main__':
    c = ConsoleClient()
    c.run_forever()
    gevent.sleep(20)