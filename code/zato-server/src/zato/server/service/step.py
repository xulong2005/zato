# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from datetime import datetime

# Zato
from zato.common.odb import model as m
from zato.common.odb import query as q
from zato.server.service import Service

# ################################################################################################################################

class ProcessInstance(object):
    """ An instance of a given process definition.
    """
    def __init__(self, cluster_id=None, proc_def_id=None):
        self.cluster_id = cluster_id
        self.proc_def_id = proc_def_id

    def init_sql(self, session):
        """ Starts a new instances of a process. Establishes pipeline and basic metadata.
        """
        proc_def = q.process_definition(session, self.cluster_id, self.proc_def_id)

        inst = m.ProcInst()
        inst.created = datetime.utcnow()
        inst.proc_def_id = proc_def.id

        session.add(inst)
        session.flush()

        for def_ in proc_def.def_pipeline:
            pipe = m.ProcInstPipeline()
            pipe.instance_id = inst.id
            pipe.def_id = proc_def.id

            session.add(pipe)

        session.commit()

# ################################################################################################################################

class MyStart(Service):
    name = 'my.start'

    ZZZ_START_NAME = 'my.service'

    def handle(self):
        with closing(self.odb.session()) as session:
            proc_defs = {}
            
            for proc_def in q.process_definition_base(session, self.server.cluster_id).\
                    filter(m.ProcDef.cluster_id == self.server.cluster_id).\
                    filter(m.ProcDefConfigStart.proc_def_id == m.ProcDef.id).\
                    filter(m.ProcDefConfigStart.service_name == self.ZZZ_START_NAME).\
                    all():

                existing = proc_defs.get(proc_def.name)
                if not existing or (existing.version < proc_def.version):
                    proc_defs[proc_def.name] = proc_def

            for proc_def in proc_defs.itervalues():
                ProcessInstance(self.server.cluster_id, proc_def.id).init_sql(session)

# ################################################################################################################################

class MyService(Service):
    name = 'my.service'

    def handle(self):
        pass

# ################################################################################################################################

class ProcGetInstances(Service):
    name = 'proc.get-instances'

    def handle(self):
        self.log_input()

# ################################################################################################################################
