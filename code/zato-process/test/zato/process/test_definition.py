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
from zato.common.test import rand_string
from zato.process.definition import ProcessDefinition

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
  Wait for signals abc on timeout 10s enter path2
  Wait for signals abc,def on timeout 10s enter path2
  Wait for signals 123,456, on timeout 10s enter path2
  Wait for signals ,789,000, on timeout 10s enter path2
  Wait for signals ,789,, on timeout 10s enter path2
  Wait for signals ,,789,, on timeout 10s enter path2
  Wait for signals ,, on timeout 10s enter path2
  Wait for signals , on timeout 10s enter path2

Path: path2
  Invoke my.service
"""

invalid_unused_paths = """
Config:

  Name: MyProcess
  Start: start.path from my.service

Path: start.path
  Invoke my.service
  Wait for signals abc,def on timeout 10s enter path2
  Wait for signals 123,456 on timeout 10s enter path4

Path: path2
  Invoke my.service

Path: path3
  Invoke my.service

Path: path4
  Invoke my.service

Path: path5
  Invoke my.service
"""

valid_one_path_only = """
Config:

  Name: My process
  Start: my.path from my.service

Pipeline:
  my.variable: str

Path: my.path
  Invoke service.name
"""

class DefinitionTestCase(TestCase):

    def setUp(self):
        self.created_by = rand_string()
        self.last_updated_by = rand_string()
        self.maxDiff = sys.maxint
        engine = sqlalchemy.create_engine('sqlite://') # I.e. :memory: in SQLite speak
        Base.metadata.create_all(engine)
        session_maker = orm.sessionmaker()
        session_maker.configure(bind=engine)
        self.session = session_maker()

    def assert_definitions_equal(self, pd1, pd2):
        self.assertDictEqual(pd1.to_canonical(), pd2.to_canonical())

    def get_process(self, process):
        pd = ProcessDefinition('en_uk')
        pd.created_by = self.created_by
        pd.last_updated_by = self.last_updated_by
        pd.text = process.strip()
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
        self.assertEquals(pd2.created_by, self.created_by)
        self.assertEquals(pd2.last_updated_by, self.last_updated_by)

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
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0001')
        self.assertEquals(result.errors[0].message, 'Processes must be named')

    def test_validate_invalid_start(self):

        # Note that we will have 2 errors because no paths are defined

        result = self.get_process(invalid_no_start).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

        result = self.get_process(invalid_no_start_service1).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

        result = self.get_process(invalid_no_start_service2).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 3)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0002')
        self.assertEquals(result.errors[0].message, 'Start node must contain both path and service')

    def test_validate_paths(self):

        # Note that we will more than 1 error because paths will be missing in some definitions

        result = self.get_process(invalid_no_paths).validate()

        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0003')
        self.assertEquals(result.errors[0].message, 'At least one path must be defined')

        result = self.get_process(invalid_paths_empty).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 1)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0004')
        self.assertEquals(result.errors[0].message, "Paths must not be empty ['my.path1', 'my.path3']")

        result = self.get_process(invalid_start_path_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 1)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[0].message, 'Start path does not exist (my.path3)')

        result = self.get_process(invalid_require_path_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path2` (Require my.path2)')

        result = self.get_process(invalid_require_else_path1_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path.foo` (Require my.path.foo else my.path2)')

        result = self.get_process(invalid_require_else_path2_does_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path.foo` (Require my.path else my.path.foo)')

        result = self.get_process(invalid_require_else_paths_do_not_exist).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 1)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[0].message, 'Path does not exist `my.path1` (Require my.path1 else my.path2)')
        self.assertEquals(result.errors[1].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[1].message, 'Path does not exist `my.path2` (Require my.path1 else my.path2)')

    def test_validate_time_units(self):
        result = self.get_process(invalid_time_unit1).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 2)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0006')
        self.assertEquals(
            result.errors[0].message, 'Invalid time expression `15a` (Wait for signal my.signal on timeout 15a enter path2)')
        self.assertEquals(result.errors[1].code, 'EPROCDEF-0006')
        self.assertEquals(
            result.errors[1].message, 'Invalid time expression `60z` (Wait for signal my.signal on timeout 60z enter path2)')

    def test_validate_commas(self):
        result = self.get_process(invalid_commas).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 6)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[1].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[2].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[3].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[4].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[5].code, 'EPROCDEF-0007')
        self.assertEquals(result.errors[0].message, 'Invalid data `123,456,` (Wait for signals 123,456, on timeout 10s enter path2)')
        self.assertEquals(result.errors[1].message, 'Invalid data `,789,000,` (Wait for signals ,789,000, on timeout 10s enter path2)')
        self.assertEquals(result.errors[2].message, 'Invalid data `,789,,` (Wait for signals ,789,, on timeout 10s enter path2)')
        self.assertEquals(result.errors[3].message, 'Invalid data `,,789,,` (Wait for signals ,,789,, on timeout 10s enter path2)')
        self.assertEquals(result.errors[4].message, 'Invalid data `,,` (Wait for signals ,, on timeout 10s enter path2)')
        self.assertEquals(result.errors[5].message, 'Invalid data `,` (Wait for signals , on timeout 10s enter path2)')

    def test_validate_unused_paths(self):
        result = self.get_process(invalid_unused_paths).validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 1)
        self.assertEquals(len(result.errors), 0)
        self.assertEquals(result.warnings[0].code, 'WPROCDEF-0001')
        self.assertEquals(result.warnings[0].message, 'Unused paths found `path3, start.path, path5`')

    def test_parse_empty(self):
        result = self.get_process('').validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 1)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0008')
        self.assertEquals(result.errors[0].message, 'Definition must not be empty')

    def test_unparseable_definition(self):
        result = self.get_process('ZZZ\nAAA').validate()
        self.assertFalse(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 6)
        self.assertEquals(result.errors[0].code, 'EPROCDEF-0001')
        self.assertEquals(result.errors[1].code, 'EPROCDEF-0002')
        self.assertEquals(result.errors[2].code, 'EPROCDEF-0003')
        self.assertEquals(result.errors[3].code, 'EPROCDEF-0005')
        self.assertEquals(result.errors[4].code, 'EPROCDEF-0009')
        self.assertEquals(result.errors[5].code, 'EPROCDEF-0009')
        self.assertEquals(result.errors[0].message, 'Processes must be named')
        self.assertEquals(result.errors[1].message, 'Start node must contain both path and service')
        self.assertEquals(result.errors[2].message, 'At least one path must be defined')
        self.assertEquals(result.errors[3].message, 'Start path does not exist ()')
        self.assertEquals(result.errors[4].message, "Could not parse line `u'ZZZ'`")
        self.assertEquals(result.errors[5].message, "Could not parse line `u'AAA'`")

    def test_dont_warn_if_one_path_only(self):
        result = self.get_process(valid_one_path_only).validate()
        self.assertTrue(result)
        self.assertEquals(len(result.warnings), 0)
        self.assertEquals(len(result.errors), 0)

    def test_highlight(self):
        proc = self.get_process(process1)

        self.assertEquals(proc.highlight(), u'<table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre> 1\n 2\n 3\n 4\n 5\n 6\n 7\n 8\n 9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29\n30\n31\n32\n33\n34\n35\n36\n37\n38\n39\n40\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n61\n62\n63\n64\n65\n66\n67\n68\n69\n70\n71\n72\n73\n74\n75\n76\n77\n78\n79\n80\n81\n82\n83\n84\n85\n86\n87\n88</pre></div></td><td class="code"><div class="highlight"><pre><span class="k">Config:</span>\n\n<span class="err">  </span><span class="k">Name:</span><span class="err"> My process</span>\n<span class="err">  </span><span class="k">Start:</span><span class="err"> order.management </span><span class="k">from</span><span class="err"> my.channel.feasibility-study</span>\n\n<span class="err">  </span><span class="k">Map service</span><span class="err"> adapter.crm.delete.user </span><span class="k">to</span><span class="err"> delete.crm</span>\n<span class="err">  </span><span class="k">Map service</span><span class="err"> adapter.billing.delete.user </span><span class="k">to</span><span class="err"> delete.billing</span>\n\n<span class="k">Pipeline:</span>\n<span class="err">  user_name: </span><span class="k">str</span>\n<span class="err">  user_id: </span><span class="k">int</span>\n<span class="err">  user_addresses: </span><span class="k">list</span>\n<span class="err">  user_social: </span><span class="k">dict</span>\n\n<span class="k">Path:</span><span class="err"> order.management</span>\n\n<span class="err">  </span><span class="k">Require</span><span class="err"> feasibility.study </span><span class="k">else</span><span class="err"> reject.order</span>\n<span class="err">  </span><span class="k">Enter</span><span class="err"> order.complete</span>\n<span class="err">  </span><span class="k">Require</span><span class="err"> abc.def</span>\n\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> patch.complete</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> signal.name </span><span class="k">on timeout</span><span class="err"> 30s </span><span class="k">enter</span><span class="err"> path.name</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> signal.name </span><span class="k">on timeout</span><span class="err"> 60m </span><span class="k">invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s patch.complete, patch.drop</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s signal.name </span><span class="k">on timeout</span><span class="err"> 30s </span><span class="k">enter</span><span class="err"> path.name</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s signal.name </span><span class="k">on timeout</span><span class="err"> 60m </span><span class="k">invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Fork to</span><span class="err"> path1, path2 </span><span class="k">under</span><span class="err"> my.fork </span><span class="k">and wait</span>\n<span class="err">  </span><span class="k">Fork to</span><span class="err"> path1, path2</span>\n\n<span class="err">  </span><span class="k">If</span><span class="err"> my.condition </span><span class="k">invoke</span><span class="err"> my.service</span>\n<span class="err">  </span><span class="k">Else</span><span class="err"> </span><span class="k">invoke</span><span class="err"> my.service2</span>\n\n<span class="err">  </span><span class="k">If</span><span class="err"> my.condition </span><span class="k">enter</span><span class="err"> my.path</span>\n<span class="err">  </span><span class="k">Else</span><span class="err"> </span><span class="k">invoke</span><span class="err"> my.path2</span>\n\n<span class="err">  </span><span class="k">Emit</span><span class="err"> my.event</span>\n<span class="err">  </span><span class="k">Set</span><span class="err"> my.key = my.value</span>\n\n<span class="k">Handler:</span><span class="err"> cease</span>\n\n<span class="err">  </span><span class="k">Require</span><span class="err"> feasibility.study </span><span class="k">else</span><span class="err"> reject.order</span>\n<span class="err">  </span><span class="k">Enter</span><span class="err"> order.complete</span>\n<span class="err">  </span><span class="k">Require</span><span class="err"> abc.def</span>\n\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> patch.complete</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> signal.name </span><span class="k">on timeout</span><span class="err"> 30s </span><span class="k">enter</span><span class="err"> path.name</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err"> signal.name </span><span class="k">on timeout</span><span class="err"> 60m </span><span class="k">invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s patch.complete, patch.drop</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s signal.name </span><span class="k">on timeout</span><span class="err"> 30s </span><span class="k">enter</span><span class="err"> path.name</span>\n<span class="err">  </span><span class="k">Wait for signal</span><span class="err">s signal.name </span><span class="k">on timeout</span><span class="err"> 60m </span><span class="k">invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> service.name</span>\n\n<span class="err">  </span><span class="k">Fork to</span><span class="err"> path1, path2 </span><span class="k">under</span><span class="err"> my.fork </span><span class="k">and wait</span>\n<span class="err">  </span><span class="k">Fork to</span><span class="err"> path1, path2</span>\n\n<span class="err">  </span><span class="k">If</span><span class="err"> my.condition </span><span class="k">invoke</span><span class="err"> my.service</span>\n<span class="err">  </span><span class="k">Else</span><span class="err"> </span><span class="k">invoke</span><span class="err"> my.service2</span>\n\n<span class="err">  </span><span class="k">If</span><span class="err"> my.condition </span><span class="k">enter</span><span class="err"> my.path</span>\n<span class="err">  </span><span class="k">Else</span><span class="err"> </span><span class="k">invoke</span><span class="err"> my.path2</span>\n\n<span class="err">  </span><span class="k">Emit</span><span class="err"> my.event</span>\n<span class="err">  </span><span class="k">Set</span><span class="err"> my.key = my.value</span>\n\n<span class="k">Handler:</span><span class="err"> amend</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.amend</span>\n\n<span class="k">Handler:</span><span class="err"> patch.complete</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.patch-complete</span>\n\n<span class="k">Handler:</span><span class="err"> drop.complete</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.on-drop-complete</span>\n\n<span class="k">Path:</span><span class="err"> feasibility.study</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.feasibility-study</span>\n\n<span class="k">Path:</span><span class="err"> order.complete</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.notify-complete</span>\n\n<span class="k">Path:</span><span class="err"> reject.order</span>\n<span class="err">  </span><span class="k">Invoke</span><span class="err"> core.order.reject</span>\n<span class="err">  </span><span class="k">Emit</span><span class="err"> order.rejected</span>\n</pre></div>\n</td></tr></table>')
        self.assertEquals(proc.highlight(mode='terminal256'), u'\x1b[38;5;28;01mConfig:\x1b[39;00m\n\n  \x1b[38;5;28;01mName:\x1b[39;00m My process\n  \x1b[38;5;28;01mStart:\x1b[39;00m order.management \x1b[38;5;28;01mfrom\x1b[39;00m my.channel.feasibility-study\n\n  \x1b[38;5;28;01mMap service\x1b[39;00m adapter.crm.delete.user \x1b[38;5;28;01mto\x1b[39;00m delete.crm\n  \x1b[38;5;28;01mMap service\x1b[39;00m adapter.billing.delete.user \x1b[38;5;28;01mto\x1b[39;00m delete.billing\n\n\x1b[38;5;28;01mPipeline:\x1b[39;00m\n  user_name: \x1b[38;5;28;01mstr\x1b[39;00m\n  user_id: \x1b[38;5;28;01mint\x1b[39;00m\n  user_addresses: \x1b[38;5;28;01mlist\x1b[39;00m\n  user_social: \x1b[38;5;28;01mdict\x1b[39;00m\n\n\x1b[38;5;28;01mPath:\x1b[39;00m order.management\n\n  \x1b[38;5;28;01mRequire\x1b[39;00m feasibility.study \x1b[38;5;28;01melse\x1b[39;00m reject.order\n  \x1b[38;5;28;01mEnter\x1b[39;00m order.complete\n  \x1b[38;5;28;01mRequire\x1b[39;00m abc.def\n\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m patch.complete\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 30s \x1b[38;5;28;01menter\x1b[39;00m path.name\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 60m \x1b[38;5;28;01minvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms patch.complete, patch.drop\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 30s \x1b[38;5;28;01menter\x1b[39;00m path.name\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 60m \x1b[38;5;28;01minvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mInvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mFork to\x1b[39;00m path1, path2 \x1b[38;5;28;01munder\x1b[39;00m my.fork \x1b[38;5;28;01mand wait\x1b[39;00m\n  \x1b[38;5;28;01mFork to\x1b[39;00m path1, path2\n\n  \x1b[38;5;28;01mIf\x1b[39;00m my.condition \x1b[38;5;28;01minvoke\x1b[39;00m my.service\n  \x1b[38;5;28;01mElse\x1b[39;00m \x1b[38;5;28;01minvoke\x1b[39;00m my.service2\n\n  \x1b[38;5;28;01mIf\x1b[39;00m my.condition \x1b[38;5;28;01menter\x1b[39;00m my.path\n  \x1b[38;5;28;01mElse\x1b[39;00m \x1b[38;5;28;01minvoke\x1b[39;00m my.path2\n\n  \x1b[38;5;28;01mEmit\x1b[39;00m my.event\n  \x1b[38;5;28;01mSet\x1b[39;00m my.key = my.value\n\n\x1b[38;5;28;01mHandler:\x1b[39;00m cease\n\n  \x1b[38;5;28;01mRequire\x1b[39;00m feasibility.study \x1b[38;5;28;01melse\x1b[39;00m reject.order\n  \x1b[38;5;28;01mEnter\x1b[39;00m order.complete\n  \x1b[38;5;28;01mRequire\x1b[39;00m abc.def\n\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m patch.complete\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 30s \x1b[38;5;28;01menter\x1b[39;00m path.name\n  \x1b[38;5;28;01mWait for signal\x1b[39;00m signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 60m \x1b[38;5;28;01minvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms patch.complete, patch.drop\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 30s \x1b[38;5;28;01menter\x1b[39;00m path.name\n  \x1b[38;5;28;01mWait for signal\x1b[39;00ms signal.name \x1b[38;5;28;01mon timeout\x1b[39;00m 60m \x1b[38;5;28;01minvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mInvoke\x1b[39;00m service.name\n\n  \x1b[38;5;28;01mFork to\x1b[39;00m path1, path2 \x1b[38;5;28;01munder\x1b[39;00m my.fork \x1b[38;5;28;01mand wait\x1b[39;00m\n  \x1b[38;5;28;01mFork to\x1b[39;00m path1, path2\n\n  \x1b[38;5;28;01mIf\x1b[39;00m my.condition \x1b[38;5;28;01minvoke\x1b[39;00m my.service\n  \x1b[38;5;28;01mElse\x1b[39;00m \x1b[38;5;28;01minvoke\x1b[39;00m my.service2\n\n  \x1b[38;5;28;01mIf\x1b[39;00m my.condition \x1b[38;5;28;01menter\x1b[39;00m my.path\n  \x1b[38;5;28;01mElse\x1b[39;00m \x1b[38;5;28;01minvoke\x1b[39;00m my.path2\n\n  \x1b[38;5;28;01mEmit\x1b[39;00m my.event\n  \x1b[38;5;28;01mSet\x1b[39;00m my.key = my.value\n\n\x1b[38;5;28;01mHandler:\x1b[39;00m amend\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.amend\n\n\x1b[38;5;28;01mHandler:\x1b[39;00m patch.complete\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.patch-complete\n\n\x1b[38;5;28;01mHandler:\x1b[39;00m drop.complete\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.on-drop-complete\n\n\x1b[38;5;28;01mPath:\x1b[39;00m feasibility.study\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.feasibility-study\n\n\x1b[38;5;28;01mPath:\x1b[39;00m order.complete\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.notify-complete\n\n\x1b[38;5;28;01mPath:\x1b[39;00m reject.order\n  \x1b[38;5;28;01mInvoke\x1b[39;00m core.order.reject\n  \x1b[38;5;28;01mEmit\x1b[39;00m order.rejected\n')

    def test_compare(self):

        # Two definitions are considered equal if their canonical
        # representations are equal. However, metadata is not taken into account
        # so as not to compare things like authors or timestamps.

        self.assertEquals(self.get_process(process1), self.get_process(process1))
        self.assertNotEquals(self.get_process(process1), self.get_process(valid_one_path_only))
