# -*- coding: utf-8 -*-

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from gevent.monkey import patch_all
patch_all()

# stdlib
from contextlib import closing
from datetime import datetime
from logging import basicConfig, getLogger, INFO
from inspect import isclass
from random import randrange
from uuid import uuid4
import warnings

# SQLAlchemy
from sqlalchemy import and_, case, create_engine, func, union, or_
from sqlalchemy.engine import reflection
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm.session import sessionmaker

# Zato
from zato.common import invalid as _invalid, ZATO_NONE
from zato.common.util import make_repr
from zato.model.data_type import DataType, DateTime, Int, NetAddress, List, Ref, Text, Wrapper
from zato.model.sql import Group, GroupTag, Item, ItemTag, SubGroup, SubGroupTag, Tag

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
_item_all_attrs=(Item.id, Item.object_id, Item.name, Item.version, Item.created_ts, Item.last_updated_ts, Item.is_active, \
        Item.is_internal, Item.parent_id)

# ################################################################################################################################

class NoSuchObject(Exception):
    """ Raised if an object was expected to exist yet could not have been found.
    """

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

    model_name = _invalid
    sql_instance_name = _invalid

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

    # What column types does this model use to hold values of its attributes? Made a class-wide attribute 
    # so that each individual query does not need to build this set each time it's needed. There will be as many values
    # in the set as there are different data types that are needed for all the attributes + the default ones
    # so if there are 5 attributes, 4 of them are text and 1 is date, there will be 2 values in the set + defaults.
    impl_types = set(_item_all_attrs)

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
            class_._model_name = class_.model_name if class_.model_name != _invalid else class_.__name__.lower()

        return class_._model_name

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def new_id(self, max=2**256, _randrage=randrange):
        """ Returns a new string with a random integer between 0 and max. It's not safe to use this integer for crypto purposes.
        """
        return str(_randrage(0, max))

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def save(self, session=None):
        model_name = self.get_model_name()

        # No ID = the instance surely doesn't exist in database
        if not self.id:

            with SessionProvider(session, self.manager) as session:

                instance_id = self.new_id()

                # Add parent instance first
                instance = Item()
                instance.object_id = '{}.{}'.format(model_name, uuid4().hex)
                instance.name = self.sql_instance_name
                instance.version = 1
                instance.id = instance_id
                instance.group_id = self.manager.user_models_group_id
                instance.sub_group_id = self.manager.user_models_sub_groups[model_name]

                session.add(instance)
                #session.flush()

                for attr_name, attr_type in self.model_attrs.iteritems():
                    model_value = getattr(self, attr_name)

                    # If model_value is still an instance of DataType it means that user never overwrote it
                    has_value = not isinstance(model_value, DataType)

                    if has_value:
                        value = Item()
                        value.id = self.new_id()
                        value.object_id = str(self.new_id())
                        value.name = attr_name
                        value.group_id = self.manager.user_models_group_id
                        value.sub_group_id = self.manager.user_models_sub_groups[model_name]
                        value.parent_id = instance_id
                        setattr(value, 'value_{}'.format(attr_type.get_impl_type()), model_value)

                        session.add(value)

                # Commit everything
                session.commit()

                # Note that external users receive object_id as self.id and id goes to self._id
                # This is in order to prevent any ID guessing, e.g. the database may be required
                # to offer strict isolation of data on multiple levels and this is one of them.
                # This becomes important if we take into account the fact that self.id is the one
                # that can be automatically serialized to external data formats, such as JSON or XML.
                self.id = instance.object_id
                self._id = instance.id

        # Else - it may potentially exist, or perhaps its ID is invalid

    @classmethod
    def by_id(class_, id=None, session=None, *args, **kwargs):
        """ Returns an object by its ID or None if it does not exist.
        """
        needs_new_session = not bool(session)

        with SessionProvider(session, class_.manager) as session:

            db_instance = session.query(*_item_all_attrs).\
                filter(Item.object_id==id).\
                one()

            db_attrs = session.query(*class_.impl_types).\
                filter(Item.parent_id==db_instance.id).\
                all()

            instance = class_()
            instance.id = db_instance.id
            instance.meta.id = db_instance.id
            instance.meta.name = db_instance.name
            instance.meta.version = db_instance.version
            instance.meta.created_ts = db_instance.created_ts
            instance.meta.last_updated_ts = db_instance.last_updated_ts
            instance.meta.is_active = db_instance.is_active
            instance.meta.is_internal = db_instance.is_internal

            for db_attr in db_attrs:
                sql_type = class_.model_attrs[db_attr.name].get_sql_type()
                if sql_type:
                    value = getattr(db_attr, sql_type)
                    setattr(instance, db_attr.name, value)

            return instance

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    @classmethod
    def filter(class_, session=None, sqlalchemy_op=and_, **kwargs):
        """ Returns result of an AND-joined compound query, e.g. one which will use multiple attributes to filter objects by.
        """
        #print(11, kwargs)

        group_id = class_.manager.user_models_group_id
        sub_group_id = class_.manager.user_models_sub_groups[class_.get_model_name()]

        with SessionProvider(session, class_.manager) as session:

            db_attrs = []

            for attr_name, value in kwargs.iteritems():
                attrs = session.query(Item.parent_id).\
                    filter(Item.group_id==group_id).\
                    filter(Item.sub_group_id==sub_group_id).\
                    filter(Item.name==attr_name).\
                    filter(class_.model_attrs[attr_name].get_sql_column()==value)
                db_attrs.append(attrs)

            db_attrs = session.query(union(*db_attrs).alias('db_attrs_union')).subquery('db_attrs')

            db_instances = session.query(Item.id, Item).\
                filter(Item.group_id==group_id).\
                filter(Item.sub_group_id==sub_group_id).\
                filter(Item.name==class_.sql_instance_name).\
                filter(Item.id==db_attrs.c.data_item_parent_id).\
                order_by(Item.id)

            #total = session.execute(db_instances).scalar()
            total_q = db_instances.statement.with_only_columns([func.count()]).order_by(None)
            print('Total', session.execute(total_q).scalar())

            #for db_instance in db_instances.all():
            db_instances.slice(50, 100).all()

        return QueryResult()

    @classmethod
    def filter_or(class_, session=None, **kwargs):
        """ Same as filter by OR-joined
        """
        return class_.filter(session, sqlalchemy_op=or_, **kwargs)

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

class QueryResult(object):
    pass

# ################################################################################################################################

class ModelManager(object):

    def __init__(self, sql_echo=False):
        db_path = '/home/dsuch/tmp/zzz.db'
        db_url = 'postgresql+pg8000://zato1:zato1@localhost/zato1'
        #db_url = 'sqlite:////home/dsuch/tmp/zzz.db'
        #from sqlalchemy.pool import QueuePool
        #engine = create_engine(db_url, echo=sql_echo, pool_size=300)
        engine = create_engine(db_url, echo=sql_echo, pool_size=150)

        self.session = sessionmaker()
        self.session.configure(bind=engine)
        self.sa_inspector = reflection.Inspector.from_engine(engine)

        # Table names, repopulated each time a model gets registered
        self.table_names = []

        # Groups and sub groups
        self.user_models_group_name = 'user.models'
        self.user_models_group_id = None
        self.user_models_sub_groups = {} # Group name -> group ID

        self.set_up_user_models_group()
        self.set_up_table_names()

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

    def set_up_table_names(self):
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

    def register(self, model_class, model_types=(DataType, Wrapper)):

        model_name = model_class.get_model_name()

        # So that models can easily issue queries
        model_class.manager = self

        # Adds if doesn't exist already
        self.add_sub_group(model_name)

        table_name = di_table_prefix + model_name

        if table_name not in self.table_names:
            logger.info('Creating table `%s`', table_name)

        '''
        self.add_sub_group(model_class.get_model_name())
        model_class.manager = self

        for name in dir(model_class):
            attr = getattr(model_class, name)
            if isinstance(attr, model_types):
                model_class.model_attrs[name] = attr
                model_class.sql_instance_name = instance_name_template.format(model_class.get_model_name())

        for k, v in model_class.model_attrs.items():

            impl_type = v.get_impl_type()
            if impl_type:
                sql_column = getattr(Item, 'value_{}'.format(impl_type))
                model_class.impl_types.add(sql_column)
                '''

# ################################################################################################################################


class Location(Model):
    facility = Ref('Facility')
    site = Ref('Site')
    city = Ref('City')
    state = Ref('State')
    country = Ref('Country')
    region = Ref('Region')

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Facility(Model):
    name = Text()

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Site(Model):
    name = Text()
    address = Text()
    facilities = List(Facility)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class City(Model):
    name = Text()
    sites = List(Site)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class State(Model):
    name = Text()
    cities = List(City)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Country(Model):
    name = Text()
    code = Text()
    states = List(State)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Region(Model):
    region_type = Int()
    region_class = Int()
    name = Text()
    countries = List(Country)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class User(Model):
    name = Text()

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Reader(Model):
    ruid = Text()
    location = Ref(Location)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Application(Model):
    name = Text()
    location = Ref(Location)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Account(Model):
    name = Text()
    users = List(User)
    readers = List(Reader)

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 

class Customer(Model):
    name = Text()
    accounts = List(Account)

# ################################################################################################################################

if __name__ == '__main__':

    mgr = ModelManager(0)

    #mgr.register(Facility)
    #mgr.register(Site)
    #mgr.register(City)
    #mgr.register(State)
    #mgr.register(Country)
    mgr.register(Region)
    #mgr.register(User)
    #mgr.register(Reader)
    #mgr.register(Application)
    #mgr.register(Account)
    #mgr.register(Customer)
    #mgr.register(Location)


    '''
    for a in range(0):

        if a % 5 == 0:
            print(a)

        for x in range(3):
            region = Region()
            region.name = 'Europe'
            region.region_class = 4
            region.region_type = 2
            region.save()
    
        for x in range(3):
            region = Region()
            region.name = 'Europe'
            region.region_class = 78
            region.region_type = 3
            region.save()
            
        for x in range(3):
            region = Region()
            region.name = 'Asia'
            region.region_class = 78
            region.region_type = 5
            region.save()
    
        for x in range(2):
            region = Region()
            region.name = 'Europe'
            region.region_class = 1
            region.region_type = 2
            region.save()
    
        for x in range(2):
            region = Region()
            region.name = 'Africa'
            region.region_class = 2
            region.region_type = 2
            region.save()

    #region_id = 'region.f1165539f58b44debbda88b89e77a1c6'
    #region = Region.by_id(region_id)

    #print(22, repr(region.name))
    #print(22, repr(region.abc.value))
    '''

    '''
    start = datetime.utcnow()

    for x in range(1):
        Region.filter(name='Eirp', region_class=78, region_type=6)

    print(datetime.utcnow() - start)
    '''