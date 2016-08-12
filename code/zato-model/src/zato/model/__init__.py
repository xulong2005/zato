# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from datetime import datetime
from inspect import isclass
from uuid import uuid4

# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

# Zato
from zato.model.sql import Group, GroupTag, Item, ItemTag, SubGroup, SubGroupTag, Tag

# ################################################################################################################################

_invalid = '<zato-invalid>'

# ################################################################################################################################

class DataType(object):
    impl_type = '<invalid>'

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

class Model(object):
    model_name = _invalid
    _model_name = None # Computed once in get_name

    def __init__(self, tags=None):
        self.id = None
        self.tags = tags or []
        self.attrs = {}

        #
        # Maps attributes that can be set by users to instances of DataType.
        # We do it here in __init__.py so that users are able to overwrite the attributes by mere assignment.
        # For instance, if we have a class such as ..
        #
        # class Bank(DataType):
        #   branch_name = Text()
        #
        # .. then branch_name will go to self.attrs and users are able to simply assign values to Python objects:
        #
        # bank = Bank()
        # bank.branch_name = 'My Street 123'
        #

        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, DataType):
                self.attrs[name] = attr

    @classmethod
    def get_name(class_):
        if not class_._model_name:
            class_._model_name = class_.model_name if class_.model_name != _invalid else class_.__name__.lower()

        return class_._model_name

# ################################################################################################################################

class List(object):
    def __init__(self, model):
        self.model = model

# ################################################################################################################################

class ModelManager(object):

    def __init__(self):
        db_path = '/home/dsuch/tmp/zzz.db'
        db_url = 'sqlite:///{}'.format(db_path)
        engine = create_engine(db_url)

        self.session = sessionmaker()
        self.session.configure(bind=engine)

        self.user_models_group_name = 'user.models'
        self.user_models_group_id = None
        self.user_models_sub_groups = {} # Group name -> group ID

        self.set_up_user_models_group()

    def set_up_user_models_group(self):

        with closing(self.session()) as session:
            g = session.query(Group).\
                filter(Group.name==self.user_models_group_name).\
                first()

            if not g:
                g = Group()
                g.name = self.user_models_group_name

                session.add(g)
                session.commit()

            self.user_models_group_id = g.id

    def add_sub_group(self, sub_group_name):

        with closing(self.session()) as session:

            sg = session.query(SubGroup).\
                filter(SubGroup.name==sub_group_name).\
                filter(SubGroup.group_id==Group.id).\
                filter(Group.name==self.user_models_group_name).\
                first()

            if not sg:
                sg = SubGroup()
                sg.name = sub_group_name
                sg.group_id = session.query(Group.id).filter(Group.name==self.user_models_group_name).one()[0]

                session.add(sg)
                session.commit()

            self.user_models_sub_groups[sub_group_name] = sg.id

            return sg

    def register(self, model_class):
        self.add_sub_group(model_class.get_name())

    def save(self, model):
        model_name = model.get_name()

        # No ID = the instance surely doesn't exist in database
        if not model.id:

            with closing(self.session()) as session:

                # Add parent instance first
                instance = Item()
                instance.object_id = '{}.{}'.format(model_name, uuid4().hex)
                instance.name = 'user.model.instance.{}'.format(model_name)
                instance.version = 1
                instance.group_id = self.user_models_group_id
                instance.sub_group_id = self.user_models_sub_groups[model_name]

                session.add(instance)
                session.flush()

                for attr_name, attr_type in model.attrs.iteritems():
                    model_value = getattr(model, attr_name)

                    # If model_value is still an instance of DataType it means that user never overwrote it
                    has_value = not isinstance(model_value, DataType)

                    if has_value:
                        value = Item()
                        value.object_id = '{}.{}.{}'.format(model_name, attr_name, uuid4().hex)
                        value.name = 'user.model.value.{}.{}'.format(model_name, attr_name)
                        value.group_id = self.user_models_group_id
                        value.sub_group_id = self.user_models_sub_groups[model_name]
                        value.parent_id = instance.id
                        setattr(value, 'value_{}'.format(attr_type.impl_type), model_value)

                        session.add(value)

                # Commit everything
                session.commit()

        # Else - it may potentially exist, or perhaps its ID is invalid

# ################################################################################################################################

class Reader(Model):
    ruid = Text(unique=True)
    last_seen = DateTime()
    last_address = NetAddress()

class ContactPerson(Model):
    name = Text()
    phone_number = List(Text())
    email = List(Text())

class Facility(Model):
    address = Text()
    contact_persons = List(ContactPerson)
    readers = List(Reader)

class Application(Model):
    name = Text(unique=True)
    last_seen = DateTime()
    token = Text()
    readers = List(Reader)
    sub_general = List(Reader)
    sub_tag_reply = List(Reader)

if __name__ == '__main__':

    mgr = ModelManager()

    mgr.register(Reader)
    mgr.register(ContactPerson)
    mgr.register(Facility)
    mgr.register(Application)

    reader = Reader()
    reader.ruid = 'abcdef'
    reader.tags = ['tag1', 'tag2', 'tag3']

    app = Application()
    app.name

    mgr.save(reader)