# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

"""
Copyright (C) 2016 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import logging
from datetime import datetime

# dictalchemy
from dictalchemy import make_class_dictable

# SQLAlchemy
from sqlalchemy import BigInteger, Boolean, Column, create_engine, Date, DateTime, Float, ForeignKey, Index, Integer, \
     LargeBinary, Numeric, Sequence, SmallInteger, String, Text, Time, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker

# Zato
Base = declarative_base()
make_class_dictable(Base)

# ################################################################################################################################

class Cluster(Base):
    __tablename__ = 'cluster'
    id = Column(Integer, Sequence('cluster_seq'), primary_key=True)

# ################################################################################################################################

class _CreatedLastUpdated(object):
    created_ts = Column(DateTime, default=datetime.utcnow)
    last_updated_ts = Column(DateTime, onupdate=datetime.utcnow)

class Group(Base, _CreatedLastUpdated):
    """ Groups common items.
    """
    __tablename__ = 'data_group'
    __table_args__ = (UniqueConstraint('cluster_id', 'name'), {})

    id = Column(Integer, Sequence('data_group_seq'), primary_key=True)
    name = Column(String(2048), unique=True, nullable=False)
    is_internal = Column(Boolean(), nullable=False, default=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=True)

# ################################################################################################################################

class SubGroup(Base, _CreatedLastUpdated):
    """ A sub-group within a larger group of items.
    """
    __tablename__ = 'data_sub_group'
    __table_args__ = (UniqueConstraint('cluster_id', 'group_id', 'name'), {})

    id = Column(Integer, Sequence('data_sub_group_seq'), primary_key=True)
    name = Column(String(2048), unique=True, nullable=False)
    is_internal = Column(Boolean(), nullable=False, default=False)

    group_id = Column(Integer, ForeignKey('data_group.id', ondelete='CASCADE'), nullable=False)
    group = relationship(Group, backref=backref('sub_groups', order_by=name, cascade='all, delete, delete-orphan'))

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=True)

# ################################################################################################################################

class Item(Base, _CreatedLastUpdated):
    """ The fundamental building block to construct configuration or runtime user-owned objects.
    Belongs to a sub-group, group and is optionally described through one or more tags.
    Column 'value' is in JSON. Some attributes are redundant for convenience - for instance, an item's group could be
    worked out through its sub-group. Likewise, tags may duplicate information that is already in 'value' - this is done
    so as not to require 'value' to be parsed on client side in order to extract data or filter by 'value's contents.
    """
    __tablename__ = 'data_item'
    __table_args__ = (
        UniqueConstraint('cluster_id', 'group_id', 'sub_group_id'),
        Index('idx_data_item_gr_sub_gr', 'group_id', 'sub_group_id'),
    {})

    # Internal ID for SQL joins
    id = Column(Text, primary_key=True)

    # External user-visible ID
    object_id = Column(Text, index=True)

    parent_id = Column(Text, ForeignKey('data_item.id', ondelete='CASCADE'), nullable=True, index=True)
    is_internal = Column(Boolean(), nullable=False, default=False)
    is_active = Column(Boolean(), nullable=False, default=True)

    # Versioning
    version = Column(Integer, index=True)

    # Foreign keys are for both groups and sub-groups

    group_id = Column(Integer, ForeignKey('data_group.id', ondelete='CASCADE'), nullable=False)
    group = relationship(Group, backref=backref('items', order_by=id, cascade='all, delete, delete-orphan'))

    sub_group_id = Column(Integer, ForeignKey('data_sub_group.id', ondelete='CASCADE'), nullable=False)
    sub_group = relationship(SubGroup, backref=backref('items', order_by=id, cascade='all, delete, delete-orphan'))

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=True)

# ################################################################################################################################

class Tag(Base, _CreatedLastUpdated):
    """ A tag that can be attached to any object.
    """
    __tablename__ = 'data_tag'
    __table_args__ = (UniqueConstraint('cluster_id', 'name'), {})

    id = Column(Integer, Sequence('data_tag_seq'), primary_key=True)
    name = Column(String(2048), unique=True, nullable=False)
    is_internal = Column(Boolean(), nullable=False, default=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=True)

# ################################################################################################################################

class GroupTag(Base, _CreatedLastUpdated):
    """ An N:N association between groups and tags.
    """
    __tablename__ = 'data_group_tag'
    __table_args__ = (UniqueConstraint('group_id', 'tag_id'), {})

    id = Column(Integer, Sequence('data_group_tag_seq'), primary_key=True)

    group_id = Column(Integer, ForeignKey('data_group.id', ondelete='CASCADE'), nullable=False)
    group = relationship(Group, backref=backref('tags', order_by=id, cascade='all, delete, delete-orphan'))

    tag_id = Column(Integer, ForeignKey('data_tag.id', ondelete='CASCADE'), nullable=False)
    tag = relationship(Tag, backref=backref('groups', order_by=id, cascade='all, delete, delete-orphan'))

# ################################################################################################################################

class SubGroupTag(Base, _CreatedLastUpdated):
    """ An N:N association between sub-groups and tags.
    """
    __tablename__ = 'data_sub_group_tag'
    __table_args__ = (UniqueConstraint('sub_group_id', 'tag_id'), {})

    id = Column(Integer, Sequence('data_sub_group_tag_seq'), primary_key=True)

    sub_group_id = Column(Integer, ForeignKey('data_sub_group.id', ondelete='CASCADE'), nullable=False)
    sub_group = relationship(SubGroup, backref=backref('tags', order_by=id, cascade='all, delete, delete-orphan'))

    tag_id = Column(Integer, ForeignKey('data_tag.id', ondelete='CASCADE'), nullable=False)
    tag = relationship(Tag, backref=backref('sub_groups', order_by=id, cascade='all, delete, delete-orphan'))

# ################################################################################################################################

class ItemTag(Base, _CreatedLastUpdated):
    """ An N:N association between items and tags.
    """
    __tablename__ = 'data_item_tag'
    __table_args__ = (UniqueConstraint('item_id', 'tag_id'), {})

    id = Column(Integer, Sequence('data_item_tag_seq'), primary_key=True)

    item_id = Column(Text, ForeignKey('data_item.id', ondelete='CASCADE'), nullable=False)
    item = relationship(Item, backref=backref('tags', order_by=id, cascade='all, delete, delete-orphan'))

    tag_id = Column(Integer, ForeignKey('data_tag.id', ondelete='CASCADE'), nullable=False)
    tag = relationship(Tag, backref=backref('items', order_by=id, cascade='all, delete, delete-orphan'))

# ################################################################################################################################