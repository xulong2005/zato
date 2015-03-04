# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
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

    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

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
    name = 'fork_to'

class ForkWait(Step):
    """ Forks out to two or more logical threads of execution and waits for their completion.
    """
    name = 'fork_to_and_wait'

class IfInvoke(Step):
    """ The 'if' part of an 'if/else' block (invokes a service).
    """
    name = 'if_invoke'

class IfEnter(Step):
    """ The 'if' part of an 'if/else' block (enters a path).
    """
    name = 'if_enter'

class ElseInvoke(Step):
    """ The 'else' part of an 'if/else' block (invokes a service).
    """
    name = 'else_invoke'

class ElseEnter(Step):
    """ The 'else' part of an 'if/else' block (enters a path).
    """
    name = 'else_enter'

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
    name = 'require'

class RequireElse(Require):
    """ Like Require but has an else path if the initial path didn't succeed.
    """
    name = 'require_else'

class WaitSignal(Step):
    """ Waits for appearance of a signal.
    """
    name = 'wait_sig'

class WaitSignalOnTimeoutEnter(Step):
    """ Waits for appearance of a signal and if it doesn't enter a path.
    """
    name = 'wait_sig_enter'

class WaitSignalOnTimeoutInvoke(Step):
    """ Waits for appearance of a signal and if it doesn't invoke a service.
    """
    name = 'wait_sig_invoke'

class WaitSignals(Step):
    """ Waits for appearance of more than one signal.
    """
    name = 'wait_sigs'

class WaitSignalsOnTimeoutEnter(Step):
    """ Waits for appearance of a signal and if they don't enter a path.
    """
    name = 'wait_sigs_enter'

class WaitSignalsOnTimeoutInvoke(Step):
    """ Waits for appearance of a signal and if they don't invoke a service.
    """
    name = 'wait_sigs_invoke'

class Emit(Step):
    """ Emits an event to subscribers waiting for it, if any.
    """
    name = 'emit'

class Set(Step):
    """ Sets a variable in pipeline
    """
    name = 'set'

class IgnoreSingal(Step):
    """ Signifies that a given signal will be ignored in a path
    even if its parent(s) would like to handle it.
    """
    name = 'ignore_signal'

class IgnoreSingals(Step):
    """ Signifies that a set of signals will be ignored in a path
    even if its parent(s) would like to handle them.
    """
    name = 'ignore_signals'

# Build a mapping of node types to actual classes
node_names = {}

for name, obj in globals().items():
    if isclass(obj) and issubclass(obj, Node):
        node_names[obj.name] = obj
