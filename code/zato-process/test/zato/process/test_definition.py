# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from unittest import TestCase

# nose
from nose.tools import eq_

# Zato
from zato.process.definition import ProcessDefinition
from zato.process.vocab import en_uk

process1 = """
Config:

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
  Wait for signals patch.complete, drop.complete
  Enter order.complete

Handler: cease
  Ignore signals: amend, *.complete

  Invoke core.order.release-resources
  Invoke core.order.on-cease

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
    def test_yaml_roundtrip(self):

        pd1 = ProcessDefinition()
        pd1.text = process1.strip()
        pd1.lang_code = 'en_uk'
        pd1.vocab_text = en_uk
        pd1.parse()

        y = pd1.to_yaml()

        pd2 = ProcessDefinition.from_yaml(y)
        raise NotImplementedError()