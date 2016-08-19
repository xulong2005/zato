# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.common import invalid as _invalid, ZATO_NONE

# ################################################################################################################################

value_column_prefix = 'value_'

# ################################################################################################################################

class DataType(object):
    impl_type = _invalid
    sql_type = impl_type

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

    def get_sql_type(self):
        return self.sql_type

# ################################################################################################################################

class Bool(DataType):
    impl_type = 'bool'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class Binary(DataType):
    impl_type = 'binary'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class Int(DataType):
    impl_type = 'int'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class SmallInt(Int):
    impl_type = 'small_int'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class BigInt(Int):
    impl_type = 'big_int'
    sql_type = value_column_prefix + impl_type

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
        return 'decimal{}'.format(self.scale)

    def get_sql_type(self, _value_column_prefix=value_column_prefix):
        return '{}decimal{}'.format(_value_column_prefix, self.scale)

# ################################################################################################################################

class Float(DataType):
    impl_type = 'float'
    sql_type = value_column_prefix + impl_type

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
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class UUID4(DataType):
    impl_type = 'text'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class NetAddress(DataType):
    impl_type = 'text'
    sql_type = value_column_prefix + impl_type

# ################################################################################################################################

class Wrapper(DataType):
    impl_type = sql_type = None

# ################################################################################################################################

class List(Wrapper):
    def __init__(self, model):
        self.model = model

# ################################################################################################################################

class Ref(Wrapper):
    def __init__(self, model):
        self.model = model

# ################################################################################################################################
