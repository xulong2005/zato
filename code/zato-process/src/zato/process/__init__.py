# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from collections import OrderedDict as _OrderedDict

class _Unsortable(tuple):
    def sort(self):
        pass # This is the point, we don't want to be sorted again

class OrderedDict(_OrderedDict):
    """ Needed so that OrderedDict instances can be represented in YAML
    using the default dict representer which sorts items. In OrderedDict
    we already know what our order should be.
    """

    def items(self):
        return _Unsortable(super(OrderedDict, self).items())