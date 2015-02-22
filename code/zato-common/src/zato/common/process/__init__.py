# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import json
from traceback import format_exc

# SpiffWorkflow
from SpiffWorkflow import Task, Workflow
from SpiffWorkflow.storage import JSONSerializer

# YAML
import yaml

class ProcessSerializer(object):
    def __init__(self, spec_data=None, state=None):
        self.spec_data = spec_data
        self.state = state
        self.impl = JSONSerializer()

    def deserialize_spec(self):
        y = yaml.load(self.spec_data)
        return self.impl.deserialize_workflow_spec(json.dumps(y))

    def serialize_state(self, process):
        return yaml.dump(yaml.load(self.impl.serialize_workflow(process)), default_flow_style=False)

    def deserialize_state(self):
        return self.impl.deserialize_workflow(json.dumps(yaml.load(self.state)))

class Process(object):
    """ Encapsulates logic responsible for executing business procesess.
    """
    def __init__(self, spec_data=None, connect_events=True):
        self.spec_data = spec_data
        self.serializer = ProcessSerializer(spec_data)
        self.spec = self.serializer.deserialize_spec() if self.spec_data else None
        self.workflow = Workflow(self.spec) if self.spec else None

        if connect_events:
            self.connect_events()

    def connect_events(self):
        for task_spec in self.workflow.spec.task_specs.itervalues():
            task_spec.ready_event.connect(self.on_ready)

    @staticmethod
    def from_workflow_spec(spec_data):
        return Process(spec_data)

    @staticmethod
    def from_workflow_spec_path(spec_path):
        return Process.from_workflow_spec(open(spec_path).read())

    @staticmethod
    def from_state(state):
        proc = Process(connect_events=False)
        proc.workflow = ProcessSerializer(state=state).deserialize_state()
        proc.connect_events()

        return proc

    @staticmethod
    def from_state_path(state_path):
        return Process.from_state(open(state_path).read())

    @property
    def done(self):
        return self.workflow.is_completed()

    def on_ready(self, workflow, task):
        if task.task_spec.name == 'second':
            raise Exception()

    def get_dump(self):
        return self.workflow.get_dump()

    def get_state(self):
        return self.serializer.serialize_state(self.workflow)

    def execute(self):
        """ Executes the next step in workflow.from_state_path
        """
        try:
            self.workflow.complete_next()
        except Exception, e:
            #print(format_exc(e))
            pass
        else:
            return True

#proc = Process.from_workflow_spec_path('wf1.yaml')

proc = Process.from_state_path('wf1-state.yaml')

print(proc.get_dump())

'''
can_continue = True

while not proc.done and can_continue:

    #print(proc.get_dump())
    can_continue = proc.execute()
    #print(can_continue)

state = proc.get_state()
print(state)
'''

'''
ps = ProcessSerializer('wf1.yaml')
spec = ps.get_process_spec()

print(spec.get_dump())

for task_spec in spec.task_specs.itervalues():
    task_spec.ready_event.connect(on_ready)

wf = Workflow(spec)
'''

#print(wf.is_completed())
#print(wf.get_dump())

#wf.complete_next()
#print(wf.is_completed())
#print(wf.get_dump())

#wf.complete_next()
#print(wf.is_completed())

#wf.complete_next()
#print(wf.is_completed())

#print()
#print(ps.get_process_state(wf))
