# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.server.service import Service

# Test support services below

# ################################################################################################################################

class String(Service):
    name = '_test.string'

    class SimpleIO:
        input_required = ('a', 'b', 'c')
        output_required = ('aa', 'bb', 'cc')

# ################################################################################################################################

class String2(Service):
    name = '_test.string2'

    class SimpleIO:
        input_required = ('a2', 'b2', 'c2')
        input_optional = ('a2a', 'b2b', 'c2c')
        output_optional = ('aa', 'bb', 'cc')

# ################################################################################################################################

class String3(Service):
    name = '_test.string3'

    class SimpleIO:
        input_optional = ('a2a', 'b2b', 'c2c')
        output_required = ('aa', 'bb', 'cc')
        output_optional = ('aaa', 'bbb', 'ccc')

# ################################################################################################################################
