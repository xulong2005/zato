# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from collections import OrderedDict
from inspect import isclass

# Zato
from zato.common.util import make_repr, new_cid
from zato.process import OrderedDict

class Node(object):
    """ A basic unit for constructing processes - parent of steps, paths and handlers.
    """
    name = 'node'

    def __init__(self, **data):
        self.id = new_cid()
        self.data = data

    def __repr__(self):
        return make_repr(self)

class Start(Node):
    """ Node represening start of a process.
    """
    name = 'start'

    def __init__(self):
        super(Start, self).__init__()
        self.path = ''
        self.service = ''

    def to_canonical(self):
        out = OrderedDict()
        out['path'] = self.path
        out['service'] = self.service

        return out

class Step(Node):
    """ A base class for steps a process is composed of.
    """
    name = 'step'

class Handler(Node):
    """ A block of steps handling one or more signals.
    """
    name = 'handler'

class Fork(Step):
    """ Forks out to two or more logical threads of execution.
    """
    name = 'fork'

    def __init__(self, parent):
        self.parent = parent

class If(Step):
    """ The 'if' part of an 'if/else' block.
    """
    name = 'if'

class Else(Step):
    """ The 'else' part of an 'if/else' block.
    """
    name = 'else'

class Enter(Step):
    """ Enters into another path or process by name.
    """
    name = 'enter'

class Invoke(Step):
    """ Invokes a service by its name.
    """
    name = 'invoke'

class Require(Step):
    """ Calls another path or process by name and ensures it completed successfully.
    """
    name = 'require2'

class RequireElse(Require):
    """ Like Require but has an else path if the initial path didn't succeed.
    """
    name = 'require1_else'

class WaitSignal(Step):
    """ Waits for appearance of a signal.
    """
    name = 'wait_sig'

class WaitSignals(Step):
    """ Waits for appearance of more than one signal.
    """
    name = 'wait_sigs3'

class Emit(Step):
    """ Emits an event to subscribers waiting for it, if any.
    """
    name = 'emit'

# Build a mapping of node types to actual classes
node_names = {}

for name, obj in globals().items():
    if isclass(obj) and issubclass(obj, Node):
        node_names[obj.name] = obj
