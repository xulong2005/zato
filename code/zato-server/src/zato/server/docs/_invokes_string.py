# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from logging import getLogger
from unittest import TestCase

# Zato
from zato.common.test import rand_int, rand_string
from zato.server.docs import Generator

logger = getLogger(__name__)

from zato.server.service import Service

# Test support services below

# ################################################################################################################################

class InvokesString(Service):
    """ InvokesString Summary
    """
    name = '_test.invokes-string'
    invokes = '_test.invokes-string2'

    class SimpleIO:
        input_required = ('a', 'b', 'c')

# ################################################################################################################################

class InvokesString2(Service):
    """ InvokesString2 Summary
    InvokesString2 Description
    """
    name = '_test.invokes-string2'
    invokes = '_test.invokes-string3'

    class SimpleIO:
        input_required = ('a2', 'b2', 'c2')
        input_optional = ('a2a', 'b2b', 'c2c')

# ################################################################################################################################

class InvokesString3(Service):
    """ InvokesString3 Summary

    InvokesString3 Description

    InvokesString3 Description2
    """
    name = '_test.invokes-string3'
    invokes = '_test.invokes-string2'

    class SimpleIO:
        input_optional = ('a2a', 'b2b', 'c2c')

# ################################################################################################################################
