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

# py
from py.code import Frame

# Zato
from zato.common.util import new_cid

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

class Client(object):
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr

        self.req_to_client = {}
        self.req_from_client = {}
        self.resp_from_client = {}

    def recv(self):
        while True:
            self.on_message(self.socket.recv(8192))

    def on_message(self, msg):
        logger.info('Got msg %r', msg)
        self.resp_from_client[msg[:2]] = msg

    def wait_for_response(self, req_id):
        while not req_id in self.resp_from_client:
            sleep(0.1)
            logging.info('%s %s', req_id, self.resp_from_client)

        return self.resp_from_client.pop(req_id)

    def send_message(self, msg, needs_response):
        data = self.socket.send(msg)
        req_id = '22'

        if needs_response:
            response = self.wait_for_response(req_id)

        logger.info('Got data %r', new_cid())

class DebugServer(object):
    def __init__(self, host='', port=19055):
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.connections = []

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.addr)
            self.socket.listen(15)

            while True:
                client_sock, addr = self.socket.accept()
                client = Client(client_sock, addr)
                self.connections.append(client)
                spawn(client.recv)
        finally:
            self.socket.close()

    def notify(self, msg):
        for client in self.connections:
            client.send_message('{} \n\n'.format(msg), True)

class App(object):

    def __init__(self):
        self.debug_server = DebugServer()

    def on_call(self, frame, event):
        frame = Frame(frame)
        if 'trace1.py' in str(frame.code.path):
            self.debug_server.notify('{} 2{}'.format(event, frame.statement))

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
