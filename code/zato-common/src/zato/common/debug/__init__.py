# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from json import loads, dumps
from time import sleep
from traceback import format_exc
import logging

# Bunch
from bunch import bunchify

# Zato
from zato.common.util import new_cid

# Base64-encoded messages contain newlines which are a no-no for us
# because messages from sockets are read line by line and each line
# is assumed to be a separate request or response.
NEWLINE_MARKER = 'ZATOZATOZATOZATO'

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, filename='debug-common.log')

logger = logging.getLogger(__name__)

# ################################################################################################################################

def json_dumps_default(obj):
    if isinstance(obj, Frame):
        return obj.to_dict()
    return str(obj)

# ################################################################################################################################

class ConnectionException(Exception):
    pass

# ################################################################################################################################

class MESSAGE_TYPE:

    class REQUEST:
        GET_STRACK_TRACE = 'get_strack_trace_req'
        NEXT = 'next_req'
        SET_ENTRY_POINT = 'set_entry_point_req'
        STEP = 'step_req'
        WELCOME = 'welcome_req'

    class RESPONSE:
        GET_STRACK_TRACE = 'get_strack_trace_resp'
        NEXT = 'next_resp'
        SET_ENTRY_POINT = 'set_entry_point_resp'
        STEP = 'step_resp'
        WELCOME = 'welcome_resp'

# ################################################################################################################################

class Message(object):
    def __init__(self, msg_id=None):
        self.msg_id = msg_id or new_cid()
        self.msg_type = None
        self.session_id = None
        self.in_reply_to = None
        self.is_sync = True
        self.data = None

    def as_dict(self):
        return {
            'msg_type': self.msg_type,
            'session_id': self.session_id,
            'msg_id': self.msg_id,
            'in_reply_to': self.in_reply_to,
            'is_sync': self.is_sync,
            'data': self.data,
        }

    def as_bunch(self):
        return bunchify(self.as_dict())

    def to_wire(self):
        return dumps(self.as_dict(), default=json_dumps_default).encode('base64').replace('\n', NEWLINE_MARKER) + '\n'

    @staticmethod
    def from_wire(data):
        msg = Message()
        data = data.replace(NEWLINE_MARKER, '\n').decode('base64')
        for k, v in loads(data).iteritems():
            setattr(msg, k, v)
        return msg

# ################################################################################################################################

class Frame(object):
    def __init__(self):
        self.obj_id = None
        self.file_name = None
        self.line = None
        self.line_no = None
        self.co_name = None
        self.args = None
        self.locals_ = None

    def to_dict(self):
        return {
            'obj_id': self.obj_id,
            'file_name': self.file_name,
            'line': self.line,
            'line_no': self.line_no,
            'co_name': self.co_name,
            'args': self.args,
            'locals_': self.locals_,
        }

# ################################################################################################################################

class Connection(object):

    def __init__(self, socket, address, session_id=None):
        self.socket = socket
        self.address = address
        self.session_id = session_id
        self.file_sock = self.socket.makefile('w',  bufsize=0)

        self.req_to_partner = {}
        self.req_from_partner = {}
        self.resp_from_partner = {}

        self.keep_running = True
        self.logger = logging.getLogger(self.__class__.__name__)

# ################################################################################################################################

    def send_sync(self, msg):

        wire_format = msg.to_wire()
        self.req_to_partner[msg.msg_id] = msg
        self.file_sock.write(wire_format)
        self.file_sock.flush()

        # TODO: Make it configurable
        max_loops = 10
        sleep_time = 0.1
        current_loop = 0

        while True:
            try:
                response = self.resp_from_partner.pop(msg.msg_id)
            except KeyError:
                sleep(sleep_time)
                current_loop += 1
                if current_loop >= max_loops:
                    error_msg = 'No response to `{!r}` from `{}`'.format(msg.as_dict(), self.address)
                    self.logger.warn(error_msg)
                    raise ConnectionException(error_msg)
            else:
                return response

# ################################################################################################################################

    def send_async(self, msg):
        raise NotImplementedError()

# ################################################################################################################################

    def send_response(self, req_msg, resp_msg=None):
        resp_msg = resp_msg or Message()

        for item in dir(MESSAGE_TYPE.REQUEST):
            if getattr(MESSAGE_TYPE.REQUEST, item) == req_msg.msg_type:
                try:
                    resp_msg_type = getattr(MESSAGE_TYPE.RESPONSE, item)
                except AttributeError:
                    raise ValueError('No response type found for request `{}`'.format(req_msg.as_dict()))

        resp_msg.msg_type = resp_msg_type
        resp_msg.session_id = req_msg.session_id
        resp_msg.in_reply_to = req_msg.msg_id
        resp_msg.is_sync = False

        self.send(resp_msg)

# ################################################################################################################################

    def send(self, msg):
        self.file_sock.write(msg.to_wire())
        self.file_sock.flush()

# ################################################################################################################################

    def main_loop(self):

        # Loop until told to stop
        while self.keep_running:

            # Each line from a client is a separate request or response
            data = self.file_sock.readline()

            if not data:
                self.keep_running = False

            else:
                self.on_message(data)

# ################################################################################################################################

    def on_message(self, data):
        try:
            msg = Message.from_wire(data)
            self.logger.info('Got message %r', msg.as_dict())
            getattr(self, 'handle_{}'.format(msg.msg_type))(msg)
        except Exception, e:
            logger.warn('Could not handle data:`%s`, e:`%s`', data, format_exc(e))

# ################################################################################################################################
