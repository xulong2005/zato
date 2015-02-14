# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from json import loads, dumps
from time import sleep
import logging

# Zato
from zato.common.util import new_cid

# Base64-encoded messages contain newlines which are a no-no for us
# because messages from sockets are read line by line and each line
# is assumed to be a separate request or response.
NEWLINE_MARKER = 'ZATOZATOZATOZATO'

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# ################################################################################################################################

class ConnectionException(Exception):
    pass

# ################################################################################################################################

class MESSAGE_TYPE:

    class REQUEST:
        WELCOME = 'welcome_req'

    class RESPONSE:
        WELCOME = 'welcome_resp'

# ################################################################################################################################

class Message(object):
    def __init__(self):
        self.msg_type = None
        self.msg_id = None
        self.session_id = None
        self.in_reply_to = None
        self.is_sync = True

    def as_dict(self):
        return {
            'msg_type': self.msg_type,
            'session_id': self.session_id,
            'msg_id': self.msg_id,
            'in_reply_to': self.in_reply_to,
            'is_sync': self.is_sync,
        }

    def to_wire(self):
        return dumps(self.as_dict()).encode('base64').replace('\n', NEWLINE_MARKER) + '\n'

    @staticmethod
    def from_wire(data):
        msg = Message()
        data = data.replace(NEWLINE_MARKER, '\n').decode('base64')
        for k, v in loads(data).iteritems():
            setattr(msg, k, v)
        return msg

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

    def send_async(self, msg):
        raise NotImplementedError()

# ################################################################################################################################

    def send_response(self, req_msg):
        msg = Message()

        for item in dir(MESSAGE_TYPE.REQUEST):
            if getattr(MESSAGE_TYPE.REQUEST, item) == req_msg.msg_type:
                try:
                    resp_msg_type = getattr(MESSAGE_TYPE.RESPONSE, item)
                except AttributeError:
                    raise ValueError('No response type found for request `{}`'.format(req_msg.as_dict()))

        msg.msg_id = new_cid()
        msg.msg_type = resp_msg_type
        msg.session_id = req_msg.session_id
        msg.in_reply_to = req_msg.msg_id
        msg.is_sync = False

        self.send(msg)

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
        msg = Message.from_wire(data)
        self.logger.info('Got message %r', msg.as_dict())

        getattr(self, 'handle_{}'.format(msg.msg_type))(msg)

# ################################################################################################################################
