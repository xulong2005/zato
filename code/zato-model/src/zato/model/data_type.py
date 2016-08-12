# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.common import invalid as _invalid

# ################################################################################################################################

class DataType(object):
    impl_type = _invalid

    def __init__(self, required=True, unique=False, default=None, choices=None):
        self.required = required
        self.unique = unique
        self.default = default
        self.choices = choices or []
        self.id = _invalid
        self.version = _invalid
        self.last_updated = _invalid
        self._value = _invalid

    def get_impl_type(self):
        return self.impl_type

# ################################################################################################################################

class Bool(DataType):
    impl_type = 'bool'

# ################################################################################################################################

class Binary(DataType):
    impl_type = 'binary'

# ################################################################################################################################

class Int(DataType):
    impl_type = 'int'

# ################################################################################################################################

class SmallInt(Int):
    impl_type = 'small_int'

# ################################################################################################################################

class BigInt(Int):
    impl_type = 'big_int'

# ################################################################################################################################

class Decimal(DataType):
    _built_in_impl_types = (2, 3, 6)

    def __init__(self, scale=2):
        self.orig_scale = scale

        if scale in self._built_in_impl_types:
            self.scale = scale
        else:
            if scale < 2:
                self.scale = 2
            elif scale in (4, 5) or scale > 6:
                self.scale = 6

    def get_impl_type(self):
        return 'decimal' + self.scale

# ################################################################################################################################

class Float(DataType):
    impl_type = 'float'

# ################################################################################################################################

class DateTime(DataType):

    def __init__(self, with_tz=False):
        self.with_tz = with_tz

    def get_impl_type(self):
        return 'date_time_tz' if self.with_tz else 'date_time'

# ################################################################################################################################

class Time(DataType):
    def __init__(self, with_tz=False):
        self.with_tz = with_tz

        def get_impl_type(self):
            return 'time_tz' if self.with_tz else 'time'

# ################################################################################################################################

class Text(DataType):
    impl_type = 'text'

# ################################################################################################################################

class UUID4(DataType):
    impl_type = 'text'

# ################################################################################################################################

class NetAddress(DataType):
    impl_type = 'text'

# ################################################################################################################################
