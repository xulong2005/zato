# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from string import whitespace

# Zato
from zato.process.path import Path
from zato.process.step import Step

class Context(object):
    pass

class ProcessDefinition(object):
    """ A definition of a process out of which new process instances are created.
    """
    def __init__(self):
        self.id = ''
        self.name = ''
        self.version = 0
        self.ext_version = ''
        self.lang = ''
        self.text = ''
        self.ctx = Context()

    def parse_en_uk_(self):
        pass

    def parse_en_uk(self):
        for line in self.text.splitlines():
            if line.strip() and line[0] not in whitespace:
                block_name = line.split()[0].replace(':', '')
                print(block_name, `line`)

    def parse(self):
        return getattr(self, 'parse_{}'.format(self.lang))()

if __name__ == '__main__':
    text = """
Context:

  Start: 'order.management' from 'my.channel.feasibility-study'

Path: order.management

  Require 'feasibility.study' or 'reject.order'
  Wait for signals 'patch.complete, drop.complete'
  Call 'order.complete'

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
  Invoke 'core.order.feasibility-study'

Path: order.complete
  Invoke 'core.order.notify-complete'

Path: reject.order
  Invoke 'core.order.reject'
  Emit 'order.rejected'
"""

    pd = ProcessDefinition()
    pd.text = text.strip()
    pd.lang = 'en_uk'
    pd.parse()