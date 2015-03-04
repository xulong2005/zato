# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import sys
from datetime import datetime
from unittest import TestCase

# arrow
from dateutil.parser import parse as dt_parse

# nose
from nose.tools import eq_

# SQLAlchemy
import sqlalchemy
from sqlalchemy import orm

# Zato
from zato.common.odb.model import Base
from zato.process.definition import ProcessDefinition
from zato.process.vocab import en_uk

# This process doesn't make much business sense but it's
# used only to check all the paths and nodes a process can go through
# so that it makes use of the whole of the vocabulary.
process1 = """
Config:

  Name: My process
  Start: order.management from my.channel.feasibility-study

  Map service adapter.crm.delete.user to delete.crm
  Map service adapter.billing.delete.user to delete.billing

Pipeline:
  user_name: str
  user_id: int
  user_addresses: list
  user_social: dict

Path: order.management

  Require feasibility.study else reject.order
  Enter order.complete
  Require abc.def

  Wait for signal patch.complete
  Wait for signal signal.name on timeout 30s enter path.name
  Wait for signal signal.name on timeout 60m invoke service.name

  Wait for signals patch.complete, patch.drop
  Wait for signals signal.name on timeout 30s enter path.name
  Wait for signals signal.name on timeout 60m invoke service.name

  Invoke service.name

  Fork to path1, path2 under my.fork and wait
  Fork to path1, path2

  If my.condition invoke my.service
  Else invoke my.service2

  If my.condition enter my.path
  Else invoke my.path2

  Emit my.event
  Set my.key = my.value

Handler: cease
  Ignore signals amend, *.complete

  Require feasibility.study else reject.order
  Enter order.complete
  Require abc.def

  Wait for signal patch.complete
  Wait for signal signal.name on timeout 30s enter path.name
  Wait for signal signal.name on timeout 60m invoke service.name

  Wait for signals patch.complete, patch.drop
  Wait for signals signal.name on timeout 30s enter path.name
  Wait for signals signal.name on timeout 60m invoke service.name

  Invoke service.name

  Fork to path1, path2 under my.fork and wait
  Fork to path1, path2

  If my.condition invoke my.service
  Else invoke my.service2

  If my.condition enter my.path
  Else invoke my.path2

  Emit my.event
  Set my.key = my.value

Handler: amend
  Invoke core.order.amend

Handler: patch.complete
  Invoke core.order.patch-complete

Handler: drop.complete
  Invoke core.order.on-drop-complete

Path: feasibility.study
  Invoke core.order.feasibility-study

Path: order.complete
  Invoke core.order.notify-complete

Path: reject.order
  Invoke core.order.reject
  Emit order.rejected
"""

class DefinitionTestCase(TestCase):

    def setUp(self):
        self.maxDiff = sys.maxint
        engine = sqlalchemy.create_engine('sqlite://') # I.e. :memory: in SQLite speak
        Base.metadata.create_all(engine)
        session_maker = orm.sessionmaker()
        session_maker.configure(bind=engine)
        self.session = session_maker()

    def assert_definitions_equal(self, pd1, pd2):
        self.assertDictEqual(pd1.to_canonical(), pd2.to_canonical())

    def get_process1(self):
        pd = ProcessDefinition()
        pd.text = process1.strip()
        pd.lang_code = 'en_uk'
        pd.vocab_text = en_uk
        pd.parse()

        return pd

    def test_yaml_roundtrip(self):
        pd = self.get_process1()
        self.assert_definitions_equal(pd, ProcessDefinition.from_yaml(pd.to_yaml()))

    def test_sql_rountrip(self):
        pd1 = self.get_process1()
        pd_id = pd1.to_sql(self.session, cluster_id=1).id

        pd2 = ProcessDefinition.from_sql(self.session, pd_id)

        # Having been just created, pd1 has no author nor time-related
        # information, hence we copy it over from pd2.
        # However, we first check that in pd2 they were indeed provided.

        self.assertIsInstance(pd2.version, int)
        self.assertGreater(pd2.version, 0)
        self.assertTrue(len(pd2.created_by) > 0)
        self.assertTrue(len(pd2.last_updated_by) > 0)

        # Makes sure it can be parsed as timestamp
        self.assertTrue(datetime.utcnow() > dt_parse(pd2.created))
        self.assertTrue(datetime.utcnow() > dt_parse(pd2.last_updated))

        pd1.id = pd2.id
        pd1.version = pd2.version
        pd1.created = pd2.created
        pd1.created_by = pd2.created_by
        pd1.last_updated = pd2.last_updated
        pd1.last_updated_by = pd2.last_updated_by

        self.assert_definitions_equal(pd1, pd2)
