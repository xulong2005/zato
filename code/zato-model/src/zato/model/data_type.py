# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# SQLAlchemy
from sqlalchemy import BigInteger, Boolean, Column, create_engine, Date, DateTime as SADateTime, Float, ForeignKey, Index, \
     Integer, LargeBinary, Numeric, Sequence, SmallInteger, String as SAString, Text as SAText, Time as SATime, UniqueConstraint

# Zato
from zato.common import invalid as _invalid, ZATO_NONE
from zato.model.sql import Item

# ################################################################################################################################

class DataType(object):
    impl_type = _invalid
    sql_type = impl_type

    def __init__(self, *args, **kwargs):
        self.dt_args = args
        self.dt_kwargs = kwargs
        self.col_kwargs = {}

        for key, value in self.dt_kwargs.items():
            if key.startswith('col_'):
                key = key.replace('col_', '', 1)
            self.col_kwargs[key] = value

        for key in self.col_kwargs:
            del self.dt_kwargs['col_' + key]

# ################################################################################################################################

class Bool(DataType):
    sql_type = Boolean

# ################################################################################################################################

class Binary(DataType):
    sql_type = LargeBinary

# ################################################################################################################################

class Int(DataType):
    sql_type = Integer

# ################################################################################################################################

class SmallInt(Int):
    sql_type = SmallInteger

# ################################################################################################################################

class BigInt(Int):
    sql_type = BigInteger

# ################################################################################################################################

class Decimal(DataType):
    sql_type = Numeric

# ################################################################################################################################

class Float(DataType):
    sql_type = Float

# ################################################################################################################################

class DateTime(DataType):
    sql_type = SADateTime

# ################################################################################################################################

class Time(DataType):
    sql_type = SATime

# ################################################################################################################################

class String(DataType):
    sql_type = SAString

# ################################################################################################################################

class Text(DataType):
    sql_type = SAText

# ################################################################################################################################

class UUID4(DataType):
    sql_type = SAText

# ################################################################################################################################

class NetAddress(DataType):
    sql_type = SAText

# ################################################################################################################################

class Wrapper(DataType):
    impl_type = sql_type = None

# ################################################################################################################################

class List(Wrapper):
    def __init__(self, model):
        self.model = model

# ################################################################################################################################

class Ref(Wrapper):
    def __init__(self, model, backref=None):
        self.model = model
        self.backref = backref

# ################################################################################################################################
