# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.common.util import make_repr, new_cid

class Node(object):
    """ A basic unit for constructing processes - parent of steps, paths and handlers.
    """
    node_type = ''

    def init(self):
        self.parent = Node()
        self.previous = Node()
        self.next = Node()
        self.name = ''
        self.id = new_cid()

    def __repr__(self):
        return make_repr(self)

class Start(Node):
    """ Node represening start of a process.
    """
    def __init__(self):
        super(Start, self).__init__()
        self.path = ''
        self.service = ''

class Step(Node):
    """ A base class for steps a process is composed of.
    """
    node_type = 'step'

class Handler(Node):
    """ A block of steps handling one or more signals.
    """
    node_type = 'handler'

class Fork(Step):
    """ Forks out to two or more logical threads of execution.
    """
    node_type = 'fork'

    def __init__(self, parent):
        self.parent = parent

class If(Step):
    """ The 'if' part of an 'if/else' block.
    """
    node_type = 'if'

    def __init__(self, parent):
        self.parent = parent

class Else(Step):
    """ The 'else' part of an 'if/else' block.
    """
    node_type = 'else'

    def __init__(self, parent):
        self.parent = parent

class Enter(Step):
    """ Enters into another path or process by name.
    """
    node_type = 'enter'

    def __init__(self, parent):
        self.parent = parent

class Invoke(Step):
    """ Invokes a service by its name.
    """
    node_type = 'invoke'

    def __init__(self, parent):
        self.parent = parent

class Require(Step):
    """ Calls another path or process by name and ensures it completed successfully.
    """
    node_type = 'require'

    def __init__(self, parent):
        self.parent = parent

class Wait(Step):
    """ Waits for appearance of one or more signals.
    """
    node_type = 'wait'

    def __init__(self, parent):
        self.parent = parent

class Emit(Step):
    """ Emits an event to subscribers waiting for it, if any.
    """
    node_type = 'emit'

    def __init__(self, parent):
        self.parent = parent
