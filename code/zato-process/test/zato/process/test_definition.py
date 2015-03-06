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

# SQLAlchemy
import sqlalchemy
from sqlalchemy import orm

# Zato
from zato.common.odb.model import Base
from zato.process.definition import Error, ProcessDefinition, Warning
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

invalid_no_name = """
Config:

  Start: my.start.path from my.service
"""

invalid_no_start = """
Config:

  Name: MyProcess
"""

invalid_no_start_service1 = """
Config:

  Name: MyProcess
  Start: my.path
"""

invalid_no_start_service2 = """
Config:

  Name: MyProcess
  Start: my.path from
"""

invalid_no_paths = """
Config:

  Name: MyProcess
  Start: order.management from my.service
"""

invalid_paths_empty = """
Config:

  Name: MyProcess
  Start: my.path2 from my.service

Path: my.path1

Path: my.path2
  Invoke my.service

Path: my.path3
"""

invalid_start_path_does_not_exist = """
Config:

  Name: MyProcess
  Start: my.path3 from my.service

Path: my.path1
  Invoke my.service

Path: my.path2
  Invoke my.service
"""

invalid_require_path_does_not_exist = """
Config:

  Name: MyProcess
  Start: my.path from my.service

Path: my.path
  Require my.path2
"""

invalid_require_else_path1_does_not_exist = """
Config:

  Name: MyProcess
  Start: my.path from my.service

Path: my.path
  Require my.path.foo else my.path2

Path: my.path2
  Invoke foo
"""

invalid_require_else_path2_does_not_exist = """
Config:

  Name: MyProcess
  Start: start.path from my.service

Path: start.path
  Require my.path else my.path.foo

Path: my.path
  Invoke foo
"""

invalid_require_else_paths_do_not_exist = """
Config:

  Name: MyProcess
  Start: start.path from my.service

Path: start.path
  Require my.path1 else my.path2

Path: my.path
  Invoke foo
"""

invalid_time_unit1 = """
Config:

  Name: MyProcess
  Start: start.path from my.service

Path: start.path
  Invoke my.service
  Wait for signal my.signal on timeout 15a enter path2
  Wait for signal my.signal on timeout 20s enter path2
  Wait for signal my.signal on timeout 30m enter path2
  Wait for signal my.signal on timeout 40h enter path2
  Wait for signal my.signal on timeout 50d enter path2
  Wait for signal my.signal on timeout 60z enter path2

Path: path2
  Invoke my.service
"""

invalid_commas = """
Config:

  Name: MyProcess
  Start: start.path from my.service

Path: start.path
  Invoke my.service
  Wait for signals abc on timeout 10s enter {service}
  Wait for signals abc,def on timeout 10s enter {service}
  Wait for signals 123,456, on timeout 10s enter {service}
  Wait for signals ,789,000, on timeout 10s enter {service}
  Wait for signals ,789,, on timeout 10s enter {service}
  Wait for signals ,,789,, on timeout 10s enter {service}
  Wait for signals ,, on timeout 10s enter {service}
  Wait for signals , on timeout 10s enter {service}

Path: path2
  Invoke my.service
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

    def get_process(self, process):
        pd = ProcessDefinition()
        pd.text = process.strip()
        pd.lang_code = 'en_uk'
        pd.vocab_text = en_uk
        pd.parse()

        return pd

    def test_yaml_roundtrip(self):
        pd = self.get_process(process1)
        self.assert_definitions_equal(pd, ProcessDefinition.from_yaml(pd.to_yaml()))

    def test_sql_rountrip(self):
        pd1 = self.get_process(process1)
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

    def test_validate_no_name(self):

        result = self.get_process(invalid_no_name).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROC-0001')
        self.assertEquals(result.errors[0].message, 'Processes must be named')

    def test_validate_invalid_start(self):

        # Note that we will have 2 errors because no paths are defined

        result = self.get_process(invalid_no_start).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROC-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

        result = self.get_process(invalid_no_start_service1).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROC-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

        result = self.get_process(invalid_no_start_service2).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROC-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

    def test_validate_paths(self):

        # Note that we will more than 1 error because paths will be missing in some definitions

        result = self.get_process(invalid_no_paths).validate()

        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROC-0003')
        self.assertEquals(result.errors[0].message, 'At least one path must be defined')

        result = self.get_process(invalid_paths_empty).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROC-0004')
        self.assertEquals(result.errors[0].message, "Paths must not be empty ['my.path1', 'my.path3']")

        result = self.get_process(invalid_start_path_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROC-0005')
        self.assertEquals(result.errors[0].message, 'Start path does not exist (my.path3)')

        result = self.get_process(invalid_require_path_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROC-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path2` (Require my.path2)')

        result = self.get_process(invalid_require_else_path1_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROC-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path.foo` (Require my.path.foo else my.path2)')

        result = self.get_process(invalid_require_else_path2_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROC-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path.foo` (Require my.path else my.path.foo)')

        result = self.get_process(invalid_require_else_paths_do_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROC-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path1` (Require my.path1 else my.path2)')
        self.assertEquals(result.errors[1].code, 'EPROC-0005')
        self.assertEquals(result.errors[1].message, 'Path does not exist `my.path2` (Require my.path1 else my.path2)')

    def test_validate_time_units(self):
        result = self.get_process(invalid_time_unit1).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROC-0006')
        self.assertEquals(
            result.errors[0].message, 'Invalid time expression `15a` (Wait for signal my.signal on timeout 15a enter path2)')
        self.assertEquals(result.errors[1].code, 'EPROC-0006')
        self.assertEquals(
            result.errors[1].message, 'Invalid time expression `60z` (Wait for signal my.signal on timeout 60z enter path2)')

    def test_validate_commas(self):
        pass