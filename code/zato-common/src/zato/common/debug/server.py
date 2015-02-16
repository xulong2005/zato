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
import bdb
import linecache
import logging
import os
import repr as repr_
import socket
import sys

# Arrow
from arrow import utcnow

# Dill
import dill

# gevent
from gevent import sleep, spawn
from gevent.pywsgi import WSGIServer
from gevent.server import StreamServer

# mx.Tools
from mx.Tools import makeref

# Zato
from zato.common.util import new_cid
from zato.common.debug import Connection, ConnectionException, Frame, Message, MESSAGE_TYPE

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

line_prefix = '\n-> '

logger = logging.getLogger(__name__)

# ################################################################################################################################

class Debugger(bdb.Bdb):
    """ Implements the actual debugger - note that we don't subclass pdb.Pdb because it's 
    """
    def __init__(self):
        bdb.Bdb.__init__(self)

        # Where we should start debugging
        self.entry_file = None 
        self.entry_line = None

    def reset(self):
        bdb.Bdb.reset(self)
        self.forget()

    def forget(self):
        self.lineno = None
        self.stack = []
        self.curindex = 0
        self.curframe = None

    def setup(self, f, t):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, t)
        self.curframe = self.stack[self.curindex][0]
        # The f_locals dictionary is updated from the actual frame
        # locals whenever the .f_locals accessor is called, so we
        # cache it here to ensure that modifications are not overwritten.
        self.curframe_locals = self.curframe.f_locals

# ################################################################################################################################

class ClientConnection(Connection):
    """ An individual connection from a client to the debugging server.
    """
    def __init__(self, *args, **kwargs):
        super(ClientConnection, self).__init__(*args, **kwargs)
        self.debugger = Debugger()
        self.debugger.reset()
        self.debugger.setup(sys._getframe(0), None)


# ################################################################################################################################

    def welcome(self):
        msg = Message()
        msg.msg_type = MESSAGE_TYPE.REQUEST.WELCOME
        msg.session_id = self.session_id

        spawn(self.send_sync, msg)

# ################################################################################################################################

    def run_forever(self):

        #self.handle_get_strack_trace_req(None)

        self.logger.info('Client connected `%s`, sid:`%s`', self.address, self.session_id)

        # Welcome the client, tell them what their session_id is
        self.welcome()

        # Blocks for as long as the client connection exists
        self.main_loop()

        self.logger.info('Client disconnected `%s`, sid:`%s`', self.address, self.session_id)

# ################################################################################################################################

    def handle_get_strack_trace_req(self, req_msg):
        stack_trace = []
        for frame, line_no in self.debugger.stack:
            file_name = self.debugger.canonic(frame.f_code.co_filename)

            locals_ = {}
            for name, obj in frame.f_locals.items():
                locals_[hex(id(obj))] = (name, obj)

            f = Frame()
            f.obj_id = hex(id(frame))
            f.file_name = file_name
            f.line = linecache.getline(file_name, line_no, frame.f_globals).strip()
            f.line_no = line_no
            f.locals_ = locals_

            stack_trace.append(f)

        msg = Message()
        msg.msg_type = MESSAGE_TYPE.RESPONSE.GET_STRACK_TRACE
        msg.in_reply_to = req_msg.msg_id
        msg.data = stack_trace

        self.send_response(req_msg, msg)

# ################################################################################################################################

    def handle_set_entry_point_req(self, msg):
        self.debugger.entry_file, self.debugger.entry_line = msg.data

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
        self.clients = []

# ################################################################################################################################

    def on_client_connected(self, socket, address):
        cc = ClientConnection(socket, address, new_cid())
        self.clients.append(cc)
        cc.run_forever()

# ################################################################################################################################

    def run(self):
        #self.on_client_connected(None, None)
        sys.settrace(self.trace)
        self.impl.serve_forever()

    def on_call(self, frame, event):
        if event == 'call':
            for cc in self.clients:
                if frame.f_code.co_filename == cc.debugger.entry_file and frame.f_code.co_name == cc.debugger.entry_line:
                    cc.debugger.setup(frame, None)

    def trace(self, frame, event, arg):
        self.on_call(frame, event)
        return self.trace

# ################################################################################################################################

class App(object):

    def __init__(self):
        self.debug_server = DebugServer()

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

    WSGIServer(('', 8088), app.on_request).serve_forever()
