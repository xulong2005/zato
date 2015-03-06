# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from datetime import datetime
from operator import attrgetter
from string import whitespace
import itertools
import json

# asteval
from asteval import Interpreter

# Bunch
from bunch import Bunch, bunchify

# ConfigObj
from configobj import ConfigObj

# parse
from parse import compile as parse_compile

# sortedcontainers
from sortedcontainers import SortedDict

# YAML
import yaml

# Zato
from zato.common.odb.model import ProcDef, ProcDefPath, ProcDefPathNode, ProcDefHandler, ProcDefHandlerNode, ProcDefPipeline, \
     ProcDefConfigStart, ProcDefConfigServiceMap, to_json
from zato.common.util import current_host, get_current_user
from zato.process import step, OrderedDict

# ################################################################################################################################

# Seconds, minutes, hours, days
TIME_UNITS = ('s', 'm', 'h', 'd')

# ################################################################################################################################

def tuple_representer(dumper, data):
    return dumper.represent_list(data)

def ordered_dict_representer(dumper, data):
    return dumper.represent_dict(data)

def sorted_dict_representer(dumper, data):
    return dumper.represent_dict(data)

def unicode_representer(dumper, data):
    return dumper.represent_str(data.encode('utf-8'))

yaml.add_representer(tuple, tuple_representer)
yaml.add_representer(OrderedDict, ordered_dict_representer)
yaml.add_representer(SortedDict, sorted_dict_representer)
yaml.add_representer(unicode, unicode_representer)

# ################################################################################################################################

class ValidationResult(object):
    def __init__(self):
        self.is_valid = False
        self.errors = []
        self.warnings = []

    def __nonzero__(self):
        return not (self.errors or self.warnings)

    def __contains__(self, item):
        container = self.errors if isinstance(item, Error) else self.warnings
        return any(elem.code == item.code for elem in container)

    def sort(self):
        # Sorts errors and warnings by their codes so it easier
        # to test them.
        self.errors.sort(key=attrgetter('code'))
        self.warnings.sort(key=attrgetter('code'))

        return self

class Warning(object):
    def __init__(self, code=None, message=None):
        self.code = code
        self.message = message

class Error(Warning):
    pass

# ################################################################################################################################

class Config(object):
    def __init__(self):
        self.name = ''
        self.start = step.Start()
        self.service_map = {}

    def handle_start(self, data):
        self.start.path = data['path']
        self.start.service = data['service']

    def handle_service_map(self, data):
        self.service_map[data['label']] = data['service']

    def handle_name(self, data):
        self.name = data['name']

class Pipeline(object):
    def __init__(self):
        self.config = {}
        self.data = {}

        # Same format for all languages supported
        self.entry_pattern = None

    def to_sql(self, session, proc_def_id):
        for key, data_type in self.config.iteritems():
            p = ProcDefPipeline()
            p.proc_def_id = proc_def_id
            p.key = key
            p.data_type = data_type().__class__.__name__
            session.add(p)
        session.flush()

class Path(object):
    model_class = ProcDefPath

    def __init__(self):
        self.name = ''
        self.nodes = []

    def to_sql(self, session, proc_def_id):

        p = self.model_class()
        p.name = self.name
        p.proc_def_id = proc_def_id

        session.add(p)
        session.flush()

        [node_item.to_sql(session, self.model_class, p.id) for node_item in self.nodes]

        session.flush()

class Handler(Path):
    model_class = ProcDefHandler

class NodeItem(object):
    def __init__(self):
        self.node_name = ''
        self.data = {}
        self.node = None
        self.line = ''

    def __cmp__(self, other):
        return self.node_name == other.node_name and sorted(self.data) == sorted(other.data)

    def create_node(self):
        self.node = step.node_names[self.node_name](**self.data)

    def to_sql(self, session, parent_class, parent_id):
        if parent_class is ProcDefPath:
            n = ProcDefPathNode()
            n.proc_def_path_id = parent_id
        else:
            n = ProcDefHandlerNode()
            n.proc_def_handl_id = parent_id

        n.node_name = self.node_name
        n.data = json.dumps(self.data)

        session.add(n)

# ################################################################################################################################

class ProcessDefinition(object):
    """ A definition of a process out of which new process instances are created.
    """
    def __init__(self):
        self.id = ''
        self.version = 0
        self.ext_version = ''
        self.lang_code = ''
        self.lang_name = '' 
        self.vocab_text = ''
        self.text = ''
        self.text_split = []
        self.eval_ = Interpreter()
        self.config = Config()
        self.pipeline = Pipeline()
        self.paths = {}
        self.handlers = {}

        self.created = ''
        self.created_by = ''

        self.last_updated = ''
        self.last_updated_by = ''

        self.vocab = Bunch()
        self.vocab.top_level = []
        self.vocab.config = {}
        self.vocab.pipeline = {}
        self.vocab.path = OrderedDict()
        self.vocab.handler = OrderedDict()

# ################################################################################################################################

    def get_block(self, start_idx):
        block = []

        for line in self.text_split[start_idx+1:]:
            line = line.strip()
            if line:
                if list(itertools.ifilter(line.startswith, self.vocab_top_level)):
                    break
                else:
                    block.append(line)

        return block

    def yield_node_info(self, start_idx, vocab_item):
        for line in self.get_block(start_idx):
            for node_name, v in self.vocab[vocab_item].items():
                result = v.parse(line)
                if result:
                    yield node_name, result.named, line
                    break

# ################################################################################################################################

    def parse_config(self, start_idx):
        for name, data, line in self.yield_node_info(start_idx, 'config'):
            getattr(self.config, 'handle_{}'.format(name))(data)

# ################################################################################################################################

    def parse_path_handler(self, start_idx, class_, node_name, target):
        elem = class_()
        elem.name = self.vocab[node_name]['name'].parse(self.text_split[start_idx]).named[node_name]

        for name, data, line in self.yield_node_info(start_idx, node_name):
            path_item = NodeItem()
            path_item.node_name = name
            path_item.data = data
            path_item.line = line
            path_item.create_node()
            elem.nodes.append(path_item)

        target[elem.name] = elem

    def parse_path(self, start_idx):
        self.parse_path_handler(start_idx, Path, 'path', self.paths)

    def parse_handler(self, start_idx):
        self.parse_path_handler(start_idx, Handler, 'handler', self.handlers)

# ################################################################################################################################

    def parse_pipeline(self, start_idx):
        for item in self.get_block(start_idx):
            named = self.pipeline.entry_pattern.parse(item).named
            self.pipeline.config[named['name']] = self.eval_(named['data_type'])

# ################################################################################################################################

    def read_vocab(self):
        conf = ConfigObj(self.vocab_text.splitlines())
        conf_bunch = bunchify(conf)

        self.lang_name = conf_bunch.main.name
        self.vocab_top_level = conf_bunch.main.top_level
        self.pipeline.entry_pattern = parse_compile(conf_bunch.pipeline.pattern)

        self.vocab['path'] = OrderedDict()

        self.vocab.path['name'] = parse_compile(conf_bunch.path.path)
        self.vocab.handler['name'] = parse_compile(conf_bunch.handler.handler)

        for name in ['config', 'path', 'handler']:
            for k, v in conf[name].iteritems():
                if k != name:
                    self.vocab[name][k] = parse_compile(v)

    def parse(self):
        self.read_vocab()
        self.text_split[:] = self.text.splitlines()

        for idx, line in enumerate(self.text_split):
            if line.strip() and line[0] not in whitespace:
                split = line.split()
                block_name = split[0].replace(':', '')
                getattr(self, 'parse_{}'.format(block_name.lower()))(idx)

# ################################################################################################################################

    def add_path_handler_to_canonical(self, out, name, source):
        for elem_name, data in source.items():
            elem = []
            for node in data.nodes:
                elem.append({'node_name':node.node_name, 'data':node.data})
            out[name][elem_name] = elem

    def to_canonical(self):
        """ Returns a canonical form of the process, i.e. a sorted dictionary
        of lists and dictionaries that can be serialized to formats such as YAML.
        """
        out = OrderedDict()
        out['config'] = OrderedDict()
        out['pipeline'] = SortedDict()
        out['path'] = SortedDict()
        out['handler'] = OrderedDict()
        out['_meta'] = OrderedDict()

        out['config']['name'] = self.config.name
        out['config']['start'] = self.config.start.to_canonical()
        out['config']['service_map'] = SortedDict(self.config.service_map.iteritems())

        out['pipeline'].update((key, value().__class__.__name__) for key, value in self.pipeline.config.items())

        self.add_path_handler_to_canonical(out, 'path', self.paths)
        self.add_path_handler_to_canonical(out, 'handler', self.handlers)

        out['_meta']['version'] = self.version
        out['_meta']['ext_version'] = self.ext_version
        out['_meta']['created'] = self.created
        out['_meta']['created_by'] = self.created_by
        out['_meta']['last_updated'] = self.last_updated
        out['_meta']['last_updated_by'] = self.last_updated_by
        out['_meta']['lang_code'] = self.lang_code
        out['_meta']['lang_name'] = self.lang_name
        out['_meta']['text'] = self.text
        out['_meta']['vocab_text'] = self.vocab_text

        return out

# ################################################################################################################################

    def extract_path_handler(self, name, source, target, class_):

        for item_name, item_data in source[name].items():

            elem = target.setdefault(item_name, class_())
            elem.name = item_name

            for step_data in item_data:
                node_item = NodeItem()
                node_item.node_name = step_data.node_name
                node_item.data = step_data.data.toDict() if isinstance(step_data.data, Bunch) else step_data.data
                node_item.create_node()
                elem.nodes.append(node_item)

    def extract_meta(self, meta):
        self.lang_code = meta.lang_code
        self.lang_name = meta.lang_name
        self.text = meta.text
        self.vocab_text = meta.vocab_text
        self.version = meta.version
        self.ext_version = meta.ext_version
        self.created = meta.created if isinstance(meta.created, basestring) else meta.created.isoformat()
        self.created_by = meta.created_by
        self.last_updated = meta.created if isinstance(meta.last_updated, basestring) else meta.last_updated.isoformat()
        self.last_updated_by = meta.last_updated_by

    def extract_config(self, config):
        self.config.name = config.name
        self.config.start.path = config.start.path
        self.config.start.service = config.start.service
        self.config.service_map.update(config.service_map.items())

    def extract_pipeline(self, pipeline):
        for k, v in pipeline.items():
            self.pipeline.config[k] = self.eval_(v)

# ################################################################################################################################

    def to_yaml(self, width=60):
        """ Serializes the canonical form of the definition to YAML.
        """
        return yaml.dump(self.to_canonical(), width=width)

# ################################################################################################################################

    @staticmethod
    def from_yaml(y):
        data = bunchify(yaml.load(y))

        pd = ProcessDefinition()

        # Meta stuff
        pd.extract_meta(data._meta)

        # Config
        pd.extract_config(data.config)

        # Pipeline
        pd.extract_pipeline(data.pipeline)

        # Path and Handler
        pd.extract_path_handler('path', data, pd.paths, Path)
        pd.extract_path_handler('handler', data, pd.handlers, Handler)

        return pd

# ################################################################################################################################

    def _get_proc_def_model(self, session, cluster_id):
        """ Any update to a definition of a process constitutes its new revision.
        Hence if we find a definition by self.config.name we create a new ProcDef
        with an incremented version. If there is none found, we treat it as revision 1.
        """
        existing = session.query(ProcDef.version).\
            filter(ProcDef.name==self.config.name).\
            filter(ProcDef.cluster_id==cluster_id).\
            order_by(ProcDef.version.desc()).\
            first()

        pd = ProcDef()
        pd.version = existing[0] + 1 if existing else 1

        return pd

# ################################################################################################################################

    def to_sql(self, session, cluster_id):

        utc_now = datetime.utcnow()
        user_host = '{}@{}'.format(get_current_user(), current_host())

        pd = self._get_proc_def_model(session, cluster_id)
        pd.cluster_id = cluster_id
        pd.name = self.config.name
        pd.ext_version = self.ext_version

        pd.created = utc_now
        pd.last_updated = utc_now

        pd.created_by = user_host
        pd.last_updated_by = user_host

        pd.lang_code = self.lang_code
        pd.lang_name = self.lang_name

        pd.text = self.text
        pd.vocab_text = self.vocab_text

        session.add(pd)
        session.flush()

        self.pipeline.to_sql(session, pd.id)
        [item.to_sql(session, pd.id) for item in itertools.chain(self.paths.values(), self.handlers.values())]

        session.flush()

        start = ProcDefConfigStart()
        start.proc_def_path_id = session.query(ProcDefPath.id).\
            filter(ProcDefPath.name==self.config.start.path).\
            filter(ProcDefPath.proc_def_id==pd.id).\
            one()[0]
        start.service_name = self.config.start.service
        start.proc_def_id = pd.id
        session.add(start)

        for label, service_name in self.config.service_map.iteritems():
            p = ProcDefConfigServiceMap()
            p.service_name = service_name
            p.label = label
            p.proc_def_id = pd.id
            session.add(p)

        session.commit()

        return pd

# ################################################################################################################################

    def _get_paths_handlers_from_sql(self, items, model, attr_name, model_attr_name):

        for item in getattr(model, model_attr_name):
            step_data = items[attr_name].setdefault(item.name, [])
            for node in item.nodes:
                step_data.append({'node_name':node.node_name, 'data':json.loads(node.data)})

    @staticmethod
    def from_sql(session, proc_def_id):
        pd_model = session.query(ProcDef).\
            filter(ProcDef.id==proc_def_id).\
            one()

        pd = ProcessDefinition()

        # Meta stuff
        pd.extract_meta(pd_model)

        # Config
        pd.config.name = pd_model.name

        # Note that currently only one service can start a process
        start_info = pd_model.def_start_paths[0]
        pd.config.start.path = start_info.proc_def_path.name
        pd.config.start.service = start_info.service_name

        # Pipeline
        pipeline = {}
        for item in pd_model.def_pipeline:
            item = to_json(item, True)['fields']
            pipeline[item['key']] = item['data_type']

        pd.extract_pipeline(pipeline)

        for item in pd_model.config_service_map:
            pd.config.service_map[item.label] = item.service_name

        items = {'path': {}, 'handler': {}}

        pd._get_paths_handlers_from_sql(items, pd_model, 'path', 'def_paths')
        pd._get_paths_handlers_from_sql(items, pd_model, 'handler', 'def_handlers')

        items = bunchify(items)

        pd.extract_path_handler('path', items, pd.paths, Path)
        pd.extract_path_handler('handler', items, pd.handlers, Handler)

        return pd

# ################################################################################################################################

    def _get_node_attrs(self, node_item, prefix):
        for attr in sorted(attr for attr in node_item.data if attr.startswith(prefix)):
            yield attr

    def _validate_path_exist(self, node_item, errors):
        for attr in self._get_node_attrs(node_item, 'path'):
            value = node_item.node.data[attr]
            if node_item.node.data[attr] not in self.paths:
                errors.append(
                    Error('EPROC-0005', 'Path does not exist `{}` ({})'.format(value, node_item.line)))

    def _validate_time_units(self, node_item, errors):
        for attr in self._get_node_attrs(node_item, 'timeout'):
            value = node_item.node.data[attr]
            if value[-1] not in TIME_UNITS:
                errors.append(
                    Error('EPROC-0006', 'Invalid time expression `{}` ({})'.format(value, node_item.line)))

    def _validate_commas(self, node_item, errors):
        # If there is any comma, the number of elements must be commas_count + 1
        for attr in self._get_node_attrs(node_item, 'signal'):
            value = node_item.node.data[attr]
            commas_count = value.count(',')
            elems = [elem for elem in value.split(',') if elem.strip()]
            if commas_count:
                if len(elems) != commas_count+1:
                    errors.append(
                        Error('EPROC-0007', 'Invalid data `{}` ({})'.format(value, node_item.line)))

    def _add_paths_user(self, node_item, paths_used):
        for attr in self._get_node_attrs(node_item, 'path'):
            paths_used.add(node_item.node.data[attr])

    def validate(self):
        """ Validates the definition of a process. The very fact that we can be called means the definition could be parsed
        however it still may contain logical issues preventing the process from starting or completing.

        Conditions checked (E=error, W=warning).

        - E: Processes must be named
        - E: Start path must be defined
        - E: At least one path must be defined
        - E: Paths must not be empty
        - E: All require/enter/fork-related/if/else nodes use paths that actually exist
        - E: Time units must be valid
        - E: All comma-separated items should be valid
        - W: No unused paths
        """
        # All paths used for various nodes
        paths_used = set()

        # Results of our work
        result = ValidationResult()

        # EPROC-0001
        # Processes must be named
        if not self.config.name:
            result.errors.append(Error('EPROC-0001', 'Processes must be named'))

        # EPROC-0002
        # Start node must contain both path and service
        if not (self.config.start.path and self.config.start.service):
            result.errors.append(Error('EPROC-0002', 'Start node must contain both path and service'))

        # EPROC-0003
        # At least one path must be defined
        if not self.paths:
            result.errors.append(Error('EPROC-0003', 'At least one path must be defined'))

        # EPROC-0004
        # Paths must not be empty
        empty = []
        for name, path in self.paths.iteritems():
            if not path.nodes:
                empty.append(name)

        if empty:
            result.errors.append(Error('EPROC-0004', 'Paths must not be empty {}'.format(
                sorted(elem.encode('utf-8') for elem in empty))))

        # EPROC-0005
        # Start/require/enter/fork/if/else-related nodes use paths that actually exist

        if self.config.start.path not in self.paths:
            result.errors.append(Error('EPROC-0005', 'Start path does not exist ({})'.format(self.config.start.path)))

        for name, path in self.paths.iteritems():
            for node_item in path.nodes:

                self._add_paths_user(node_item, paths_used)

                # EPROC-0005
                if isinstance(node_item.node, (step.Require, step.RequireElse, step.Enter, step.Fork,
                        step.IfEnter, step.ElseEnter, step.WaitSignalsOnTimeoutEnter, step.WaitSignalsOnTimeoutInvoke)):
                    self._validate_path_exist(node_item, result.errors)

                # EPROC-0006
                # Time units must be valid

                if isinstance(node_item.node, (step.WaitSignalOnTimeoutEnter,
                        step.WaitSignalOnTimeoutInvoke, step.WaitSignalsOnTimeoutEnter, step.WaitSignalsOnTimeoutInvoke)):
                    self._validate_time_units(node_item, result.errors)

                # EPROC-0007
                # All comma-separated items must be valid
                if isinstance(node_item.node, (step.WaitSignals,
                        step.WaitSignalsOnTimeoutEnter, step.WaitSignalsOnTimeoutInvoke)):
                    self._validate_commas(node_item, result.errors)

        # WPROC-0001
        # No unused paths
        unused = set(self.paths) - paths_used
        if unused:
            result.warnings.append(Warning('WPROC-0001', 'Unused paths found `{}`'.format(
                ', '.join(elem.encode('utf-8') for elem in unused))))

        return result.sort()

# ################################################################################################################################

    def highlight(self):
        pass