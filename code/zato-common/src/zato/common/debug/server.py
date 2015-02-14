# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# gevent.monkey
from gevent.monkey import patch_all, patch_thread
patch_all()

# stdlib
import logging
import socket
import sys

# Arrow
from arrow import utcnow

# gevent
from gevent import sleep, spawn
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer

# py
from py.code import Frame

# Zato
from zato.common.util import new_cid
from zato.common.debug import Connection, ConnectionException, Message, MESSAGE_TYPE

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# ################################################################################################################################

class ClientConnection(Connection):
    """ An individual connection from a client to the debugging server.
    """

# ################################################################################################################################

    def welcome(self):
        msg = Message()
        msg.msg_type = MESSAGE_TYPE.REQUEST.WELCOME
        msg.msg_id = new_cid()
        msg.session_id = self.session_id

        spawn(self.send_sync, msg)

# ################################################################################################################################

    def run_forever(self):

        self.logger.info('Client connected `%s`, sid:`%s`', self.address, self.session_id)

        # Welcome the client, tell them what their session_id is
        self.welcome()

        # Blocks for as long as the client connection exists
        self.main_loop()

        self.logger.info('Client disconnected `%s`, sid:`%s`', self.address, self.session_id)

# ################################################################################################################################

    def handle_welcome_resp(self, msg):
        self.resp_from_partner[msg.in_reply_to] = msg

# ################################################################################################################################

class DebugServer(object):
    """ A TCP server for debugging clients to connect to.
    """
    def __init__(self, host='localhost', port=19055):
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.impl = StreamServer((host, port), self.on_client_connected)
        self.connections = []

# ################################################################################################################################

    def on_client_connected(self, socket, address):
        cc = ClientConnection(socket, address, new_cid())
        cc.run_forever()

# ################################################################################################################################

    def run(self):
        self.impl.serve_forever()

# ################################################################################################################################

class App(object):

    def __init__(self):
        self.debug_server = DebugServer()

    def on_call(self, frame, event):
        #if event == 'line':
        #    frame = Frame(frame)
        #    if 'server.py' in str(frame.code.path):
        #        print(frame.statement)
        #        self.debug_server.notify('{} {}'.format(event, frame.statement).encode('base64'))
        pass

    def trace(self, frame, event, arg):
        self.on_call(frame, event)
        return self.trace

    def handle(self):
        a = 1
        b = 2
        logger.info(456)

    def on_request(self, env, start_response):
        path = env['PATH_INFO']
        self.handle()

        start_response(b'200 OK', [(b'Content-Type', b'text/plain')])
        return [b'Hello world\n']

if __name__ == '__main__':
    app = App()

    spawn(app.debug_server.run)

    sleep(1)

    sys.settrace(app.trace)

    WSGIServer(('', 8088), app.on_request).serve_forever()
