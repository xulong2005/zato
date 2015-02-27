# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from cStringIO import StringIO
from string import whitespace
import itertools

# addict
from addict import Dict

# asteval
from asteval import Interpreter

# Bunch
from bunch import bunchify

# ConfigObj
from configobj import ConfigObj

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
    def __init__(self, prefix, pattern):
        self.prefix = prefix
        self.pattern = parse_compile(pattern)

class Pipeline(object):
    def __init__(self):
        self.config = {}
        self.data = {}

        # Same format for all languages supported
        self.entry_pattern = parse_compile('ZATO_DOES_NOT_EXIST')

class PathItem(object):
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
        self.lang_code = ''
        self.lang_name = '' 
        self.vocab_text = ''
        self.text = ''
        self.text_split = self.text.splitlines()
        self._eval = Interpreter()
        self.config = Config()
        self.pipeline = Pipeline()
        self.paths = {}

        self.vocab = Dict()
        self.vocab.top_level = []
        self.vocab.config = {}
        self.vocab.pipeline = {}
        self.vocab.path = {}
        self.vocab.handler = {}

        #    'start': ConfigItem('Start:', "Start: {path} from {service}"),
        #    'service_map': ConfigItem('Map service', "Map service {service} to {label}"),
        #}

# ################################################################################################################################

    def get_block(self, start_idx):
        block = []
        keep_running = True

        for line in self.text_split[start_idx+1:]:
            line = line.strip()
            if line:
                if list(itertools.ifilter(line.startswith, self.vocab_top_level)):
                    break
                else:
                    block.append(line)

        return block

# ################################################################################################################################

    def parse_config(self, start_idx):
        for line in self.get_block(start_idx):
            for name, item in self.vocab.config.iteritems():
                if line.startswith(item.prefix):
                    result = item.pattern.parse(line)
                    getattr(self.config, 'handle_{}'.format(name))(result.named)

# ################################################################################################################################

    def parse_path(self, start_idx):
        return
        block = self.get_block(start_idx)
        #print(block)

# ################################################################################################################################

    def parse_handler(self, start_idx):
        #print('Handler', start_idx)
        pass

# ################################################################################################################################

    def parse_pipeline(self, start_idx):
        for item in self.get_block(start_idx):
            named = self.pipeline.entry_pattern.parse(item).named
            self.pipeline.config[named['name']] = self._eval(named['data_type'])

# ################################################################################################################################

    def read_vocab(self):
        conf = bunchify(ConfigObj(self.vocab_text.splitlines()))

        self.lang_name = conf.main.name
        self.vocab_top_level = conf.main.top_level
        self.pipeline.entry_pattern = parse_compile(conf.pipeline.pattern)

    def parse(self):
        self.read_vocab()
        self.text_split[:] = self.text.splitlines()

        for idx, line in enumerate(self.text_split):
            if line.strip() and line[0] not in whitespace:
                split = line.split()
                block_name = split[0].replace(':', '')
                getattr(self, 'parse_{}'.format(block_name.lower()))(idx)

# ################################################################################################################################

if __name__ == '__main__':

    proc_path = './proc.txt'
    lang_code = 'en_uk'

    text = open(proc_path).read()
    vocab_text = open('vocab-{}.ini'.format(lang_code)).read()

    pd = ProcessDefinition()
    pd.text = text.strip()
    pd.lang_code = lang_code
    pd.vocab_text = vocab_text
    pd.parse()

    #print(pd.config.start)
    #print(pd.config.service_map)

    #print(pd.pipeline.config)
    #print(pd.pipeline.data)