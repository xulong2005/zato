# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from string import whitespace
import itertools

# addict
from addict import Dict

# parse
from parse import compile as parse_compile

# Zato
from zato.process.path import Path
from zato.process.step import Start

class Config(object):
    def __init__(self):
        self.start = Start()
        self.start.init()
        self.start.name = 'Start'
        self.start.parent = None
        self.start.previous = None
        self.service_map = {}

    def handle_start(self, data):
        self.start.path = data['path']
        self.start.service = data['service']

    def handle_service_map(self, data):
        self.service_map[data['label']] = data['service']

class ConfigItem(object):
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = parse_compile(pattern)

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
        self.text_split = self.text.splitlines()
        self.config = Config()

        # Same format for all languages supported
        self.pipeline_entry_pattern = '{name}: {data_type}'

        self.en_uk_top_level = ('Config:', 'Path:', 'Handler:', 'Pipeline:')
        self.en_uk_config = {
            'Start:': ConfigItem('start', "Start: '{path}' from '{service}'"),
            'Map service': ConfigItem('service_map', "Map service '{service}' to '{label}'"),
        }

# ################################################################################################################################

    def get_block(self, start_idx):
        block = []
        keep_running = True

        for line in self.text_split[start_idx+1:]:
            line = line.strip()
            if line:
                if list(itertools.ifilter(line.startswith, self.en_uk_top_level)):
                    break
                else:
                    block.append(line)

        return block

# ################################################################################################################################

    def parse_en_uk_config(self, start_idx):
        config = Config()
        block = self.get_block(start_idx)

        for line in block:
            for prefix, item in self.en_uk_config.iteritems():
                if line.startswith(prefix):
                    result = item.pattern.parse(line)
                    getattr(config, 'handle_{}'.format(item.name))(result.named)

        print(config.service_map)
        print(config.start)

# ################################################################################################################################

    def parse_en_uk_path(self, start_idx):
        #print('Path', start_idx)
        pass

# ################################################################################################################################

    def parse_en_uk_handler(self, start_idx):
        #print('Handler', start_idx)
        pass

# ################################################################################################################################

    def parse_en_uk_pipeline(self, start_idx):
        #print('Pipeline', start_idx)
        pass

# ################################################################################################################################

    def parse_en_uk(self):
        self.text_split[:] = self.text.splitlines()
        for idx, line in enumerate(self.text_split):
            if line.strip() and line[0] not in whitespace:
                split = line.split()
                block_name = split[0].replace(':', '')
                getattr(self, 'parse_{}_{}'.format(self.lang, block_name.lower()))(idx)

# ################################################################################################################################

    def parse(self):
        return getattr(self, 'parse_{}'.format(self.lang))()
        
# ################################################################################################################################

if __name__ == '__main__':
    text = """
Config:

  Start: 'order.management' from 'my.channel.feasibility-study'

  Map service 'adapter.crm.delete.user' to 'delete.crm'
  Map service 'adapter.billing.delete.user' to 'delete.billing'

Pipeline:
  user_name: str
  user_id: int
  user_addresses: list
  user_social: dict

Path: order.management

  Require 'feasibility.study' or 'reject.order'
  Wait for signals 'patch.complete, drop.complete'
  Enter 'order.complete'

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