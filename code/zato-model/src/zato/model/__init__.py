# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from logging import basicConfig, getLogger, INFO
from inspect import isclass
from random import randrange
from uuid import uuid4
import warnings

# Alembic
from alembic.migration import MigrationContext
from alembic.operations import Operations

# Bunch
from bunch import bunchify

# SQLAlchemy
from sqlalchemy import Column, create_engine, ForeignKey, ForeignKeyConstraint, func, Integer, INTEGER, or_, Sequence, text, Text as SAText
from sqlalchemy.engine import reflection
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql import true as sa_true

# Zato
from zato.common import invalid as _invalid
from zato.common.util import make_repr, new_cid
from zato.model.data_type import DataType, Int, List, Ref, String, Text, Wrapper
from zato.model.sql import Base, Group, Item, SubGroup

warnings.filterwarnings('ignore',
                        r'^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively\, '
                        'and SQLAlchemy must convert from floating point - rounding errors and other '
                        'issues may occur\. Please consider storing Decimal numbers as strings or '
                        'integers on this platform for lossless storage\.$',
                        SAWarning, r'^sqlalchemy\.sql\.type_api$')

# ################################################################################################################################

logger = getLogger(__name__)

basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s')

# ################################################################################################################################

instance_name_template = 'user.model.instance.{}'
di_table_prefix = 'di_'

# ################################################################################################################################

_item_by_id_attrs=(Item.id,)
_item_all_attrs=(Item.id.label('zato_di_id'), Item.object_id.label('zato_di_object_id'),
                 Item.version.label('zato_di_version'), Item.created_ts.label('zato_di_created_ts'),
                 Item.last_updated_ts.label('zato_di_last_updated_ts'),
                 Item.is_active.label('zato_di_is_active'), Item.is_internal.label('zato_di_is_internal'),
                 Item.parent_id.label('di_zato_parent_id'))


# ################################################################################################################################

class QueryResult(object):
    __slots__ = ['total', 'page_current', 'page_prev', 'page_next', 'page_last']

    def __init__(self):
        self.total = 0
        self.page_current = 0
        self.page_prev = 0
        self.page_next = 0
        self.page_last = 0

# ################################################################################################################################

class NoSuchObject(Exception):
    """ Raised if an object was expected to exist yet could not have been found.
    """

# ################################################################################################################################

def model_name_from_class_name(class_name):
    """ Does not do much at the moment but may be made more sophisticated if need be.
    """
    class_name = class_name.__name__ if isclass(class_name) else class_name
    return class_name.lower()

# ################################################################################################################################

class ModelMeta(object):
    __slots__ = ('created_ts', 'last_updated_ts', 'is_internal', 'is_active', 'version', 'id', 'name')

    def __init__(self):
        self.created_ts = None
        self.last_updated_ts = None
        self.is_internal = None
        self.is_active = None
        self.version = None
        self.id = None
        self.name = None

    def __repr__(self):
        return make_repr(self)

# ################################################################################################################################

class Model(object):

    # Will be set in subclassess
    model_name = _invalid

    # Each subclass has its own
    table = table_name = _invalid

    # Computed once in get_name
    _model_name = None

    # ModelManager instance
    manager = None

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
    model_attrs = {}


    def __init__(self, tags=None):

        # User-facing one
        self.id = None

        # Internal, SQL-based one
        self._id = None
        self.meta = ModelMeta()
        self.tags = tags or []

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    @classmethod
    def get_model_name(class_):
        if not class_._model_name:
            class_._model_name = class_.model_name if class_.model_name != _invalid else \
                model_name_from_class_name(class_.__name__)

        return class_._model_name

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def new_id(self, max=2**256, _randrage=randrange):
        """ Returns a new string with a random integer between 0 and max. It's not safe to use this integer for crypto purposes.
        """
        return str(_randrage(0, max)).encode('hex')

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def save(self, session=None, new_cid=new_cid):
        model_name = self.get_model_name()

        # No ID = the instance surely doesn't exist in database
        if not self.id:

            with SessionProvider(session, self.manager) as session:

                instance_id = new_cid()

                # Add parent instance first
                item = Item()
                item.object_id = '{}.{}'.format(model_name, uuid4().hex)
                item.version = 1
                item.id = instance_id
                item.group_id = self.manager.user_models_group_id
                item.sub_group_id = self.manager.user_models_sub_groups[model_name]

                value_instance = self.table()

                for attr_name, attr_type in self.model_attrs.iteritems():

                    value = getattr(self, attr_name)

                    # If model_value is still an instance of DataType it means that user never overwrote it
                    has_value = not isinstance(value, DataType)

                    if has_value:
                        setattr(value_instance, attr_name, value)

                value_instance.data_item = item

                session.add(item)
                session.add(value_instance)

                # Commit everything
                session.commit()

                # Note that external users receive object_id as self.id and id goes to self._id
                # This is in order to prevent any ID guessing, e.g. the database may be required
                # to offer strict isolation of data on multiple levels and this is one of them.
                # This becomes important if we take into account the fact that self.id is the one
                # that can be automatically serialized to external data formats, such as JSON or XML.
                self.id = item.object_id
                self._id = item.id

        # Else - it may potentially exist, or perhaps its ID is invalid

    @classmethod
    def by_id(class_, id=None, session=None, *args, **kwargs):
        """ Returns an object by its ID or None if it does not exist.
        """
        with SessionProvider(session, class_.manager) as session:

            db_instance = session.query(class_.table, *_item_all_attrs).\
                filter(Item.object_id==id).\
                filter(Item.id==class_.table.item_id).\
                one()

            attrs = getattr(db_instance, class_.table_name)

            instance = class_()
            instance.id = db_instance.zato_di_id
            instance.meta.id = db_instance.zato_di_id
            instance.meta.name = db_instance.zato_di_name
            instance.meta.version = db_instance.zato_di_version
            instance.meta.created_ts = db_instance.zato_di_created_ts
            instance.meta.last_updated_ts = db_instance.zato_di_last_updated_ts
            instance.meta.is_active = db_instance.zato_di_is_active
            instance.meta.is_internal = db_instance.zato_di_is_internal

            for attr_name, attr_value in class_.model_attrs.items():
                if isinstance(attr_value, Wrapper):
                    continue
                setattr(instance, attr_name, getattr(attrs, attr_name))

            return instance

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    @classmethod
    def filter(class_, session=None, _is_and=True, _list_values=(list, tuple), **kwargs):
        """ Returns result of an AND-joined compound query, e.g. one which will use multiple attributes to filter objects by.
        """
        group_id = int(class_.manager.user_models_group_id)
        sub_group_id = int(class_.manager.user_models_sub_groups[class_.get_model_name()])

        with SessionProvider(session, class_.manager) as session:

            db_instances = session.query(class_.table, *_item_all_attrs).\
                filter(Item.group_id==group_id).\
                filter(Item.sub_group_id==sub_group_id).\
                filter(Item.id==class_.table.item_id)

            if _is_and:
                for name, value in kwargs.iteritems():
                    if name in class_.model_attrs:
                        db_instances = db_instances.filter(getattr(class_.table, name)==value)
            else:
                or_criteria = []

                for name, values in kwargs.iteritems():
                    values = values if isinstance(values, _list_values) else [values]
                    if name in class_.model_attrs:
                        column = getattr(class_.table, name)
                        for value in values:
                            or_criteria.append(column.__eq__(value))

                db_instances = db_instances.filter(or_(*or_criteria))

            db_instances = db_instances.order_by(Item.id)

            total_q = db_instances.statement.with_only_columns([func.count()]).order_by(None)
            total = session.execute(total_q).scalar()

        query_result = QueryResult()
        query_result.total = total

        return query_result

    @classmethod
    def filter_or(class_, session=None, **kwargs):
        """ Same as filter by OR-joined
        """
        return class_.filter(session, _is_and=False, **kwargs)

# ################################################################################################################################

class SessionProvider(object):

    def __init__(self, session, manager):
        self.needs_new_session = not bool(session)
        self.session = manager.session() if self.needs_new_session else session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):

        #  No matter if exception or not, always close a session if we opened it ourselves
        if self.needs_new_session:
            self.session.close()

        return not exc_type

# ################################################################################################################################

class ModelManager(object):

    def __init__(self, db_url, sql_echo=False):
        #db_url = 'postgresql+pg8000://zato1:zato1@localhost/zato1'
        kwargs = {} if 'sqlite' in db_url else {'pool_size':150}
        self.engine = create_engine(db_url, echo=sql_echo, **kwargs)

        self.session = sessionmaker()
        self.session.configure(bind=self.engine)
        self.sa_inspector = reflection.Inspector.from_engine(self.engine)

        # SA table objects, keyed by their names
        self.models = {}

        # Table names, repopulated each time a model gets registered
        self.table_names = []

        # Groups and sub groups
        self.user_models_group_name = 'user.models'
        self.user_models_group_id = None
        self.user_models_sub_groups = {} # Group name -> group ID

        self.set_up_user_models_group()
        self.update_table_names()

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def update_table_names(self):
        self.table_names = self.sa_inspector.get_table_names()

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

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

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

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

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def get_table_object(self, name, model_class):

        model = type(str(name), (Base,), {
            '__tablename__':name,
            '__table_args__':None,
            'id': Column(Integer, Sequence('{}_seq'.format(name)), primary_key=True),
            'item_id': Column(SAText, ForeignKey('data_item.id', ondelete='CASCADE'), nullable=False),
            'data_item': relationship('Item')
        })

        for column_name, column_info in model_class.model_attrs.items():

            # List wrappers are not handled by SQLAlchemy
            if isinstance(column_info, Wrapper):
                continue

            sql_type = column_info.sql_type
            dt_args = column_info.dt_args
            dt_kwargs = column_info.dt_kwargs
            col_kwargs = column_info.col_kwargs
            setattr(model, column_name, Column(sql_type(*dt_args, **dt_kwargs), **col_kwargs))

        self.models[name] = model

        return model

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def create_table(self, name, model_class):
        logger.info('Creating table `%s` for `%s` in `%s`', name, model_class, self.engine.url)

        table = self.get_table_object(name, model_class)
        Base.metadata.create_all(self.engine)

        return table

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def register_tables(self, model_classes, model_types=(DataType, Wrapper)):
        """ Registers SQLAlchemy-backed table for given models.
        """
        for model_class in model_classes:
            model_name = model_class.get_model_name()

            # So that models can easily issue queries
            model_class.manager = self

            # Adds if doesn't exist already
            self.add_sub_group(model_name)

            model_attrs = {}
            setattr(model_class, 'model_attrs', model_attrs)

            for name in dir(model_class):
                attr = getattr(model_class, name)
                if isinstance(attr, model_types):
                    model_attrs[name] = attr

            table_name = di_table_prefix + model_name

            if table_name not in self.table_names:
                table = self.create_table(table_name, model_class)
                self.update_table_names()
            else:
                table = self.get_table_object(table_name, model_class)

            setattr(model_class, 'table', table)
            setattr(model_class, 'table_name', table_name)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def _has_fkey(self, model, model_fkeys, referred_table, referred_columns):
        """ Returns True if a given model references another table through a foreign key.
        """
        for fkey in bunchify(model_fkeys):
            if fkey.referred_table == referred_table and fkey.referred_columns == ['id']:
                return True

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def _add_fkey(self, model, model_name, ref_model_name, fkey_name):
        """ Adds a foreign from model to the target table's ID.
        """
        op = Operations(MigrationContext.configure(self.engine.connect()))

        logger.info('Adding fkey for %s %s %s', model_name, ref_model_name, fkey_name)

        with op.batch_alter_table(model_name) as batch:

            fkey = ForeignKey('{}.id'.format(ref_model_name), name='fk_{}'.format(fkey_name), ondelete='CASCADE')
            #fkey = ForeignKeyConstraint([fkey_name], ['{}.id'.format(ref_model_name)], name='fk_{}'.format(fkey_name), ondelete='zzz')
            column = Column(fkey_name, Integer, fkey, nullable=False)
            batch.add_column(column)

        op.create_index(str('ix_{}_{}'.format(model_name, fkey_name)), str(model_name), [str(fkey_name)], unique=True)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def create_constraints(self, name, model_class):

        di_name = 'di_{}'.format(name)
        model = self.models[di_name]
        model_fkeys = self.sa_inspector.get_foreign_keys(di_name)

        for column_name, column_info in model_class.model_attrs.items():

            # Ref wrappers are translated into foreign keys
            if isinstance(column_info, Ref):

                ref_model_name = di_table_prefix + model_name_from_class_name(column_info.model)
                fkey = ref_model_name + '_id'
                setattr(model, fkey,
                        Column(Integer, ForeignKey('{}.id'.format(ref_model_name), ondelete='CASCADE'), nullable=False))

                if not self._has_fkey(model, model_fkeys, ref_model_name, fkey):
                    self._add_fkey(model, di_name, ref_model_name, fkey)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def register_constraints(self, model_classes):
        """ Registers SQL constrains for models given on input.
        """
        for model_class in model_classes:
            self.create_constraints(model_class.get_model_name(), model_class)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def register(self, model_classes):
        self.register_tables(model_classes)
        self.register_constraints(model_classes)

# ################################################################################################################################
