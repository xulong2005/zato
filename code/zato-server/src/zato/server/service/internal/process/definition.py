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
from zato.common import KVDB
from zato.common.broker_message import PROCESS
from zato.common.odb.model import ProcDef
from zato.common.odb.query import process_definition, process_definition_list
from zato.process.definition import ProcessDefinition
from zato.process.vocab import vocab_dict
from zato.server.service import List
from zato.server.service.internal import AdminService, AdminSIO
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

elem = 'process_definition'
model = ProcDef
label = 'a process definition'
broker_message = PROCESS
broker_message_prefix = 'DEFINITION_'
list_func = process_definition_list
skip_input_params = ['created']
publish_on_delete = False

# ################################################################################################################################

def response_hook(self, input, instance, attrs, action):
    if action == 'get_list':
        for item in self.response.payload:
            item.created = item.created.isoformat()
            item.last_updated = item.last_updated.isoformat()

def delete_hook(self, input, instance, attrs):
    self.kvdb.conn.sadd(KVDB.PROC_DELETED, input.id)

# ################################################################################################################################

class GetList(AdminService):
    __metaclass__ = GetListMeta

# ################################################################################################################################

class Create(AdminService):
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_create_request'
        response_elem = 'zato_process_definition_create_response'
        input_required = ('created_by', 'lang_code', 'text', 'cluster_id')
        input_optional = ('ext_version',)
        output_required = ('id', 'msg')

    def handle(self):
        pd = ProcessDefinition(self.request.input.lang_code)
        pd.last_updated_by = self.request.input.get('created_by')
        pd.is_active = True

        for name in self.SimpleIO.input_required + self.SimpleIO.input_optional:
            setattr(pd, name, self.request.input[name])

        pd.parse()

        with closing(self.odb.session()) as session:
            pd.to_sql(session, self.request.input.cluster_id)

        self.response.payload.id = pd.id
        self.response.payload.msg = 'OK, created successfully'

class Edit(AdminService):
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_edit_request'
        response_elem = 'zato_process_definition_edit_response'
        input_required = ('id', 'last_updated_by', 'lang_code', 'text', 'cluster_id')
        input_optional = ('ext_version',)
        output_required = ('id', 'msg')

    def _set_attrs(self, instance):
        for name in self.SimpleIO.input_required + self.SimpleIO.input_optional:
            setattr(instance, name, self.request.input[name])

    def _add_new_version(self, new, session):
        new.created_by = new.last_updated_by
        new_model = new.to_sql(session, self.request.input.cluster_id)
        return new_model.id, 'OK, created a new version ({})'.format(new_model.version)

    def handle(self):

        new = ProcessDefinition(self.request.input.lang_code)
        new.last_updated_by = self.request.input.get('last_updated_by')
        new.is_active = True
        self._set_attrs(new)
        new.parse()

        new_id = None

        with closing(self.odb.session()) as session:
            existing_pd = ProcessDefinition.from_sql(session, self.request.input.id)
            common_attrs_equal = new.config.name == existing_pd.config.name and new.ext_version == existing_pd.ext_version

            # Nothing has changed at all
            if new == existing_pd and common_attrs_equal:
                self.logger.warn(1)
                msg = 'Note: definition intact, leaving as is without saving'

            # Something must have been updated
            else:

                # If only common attributes are equal it means that other one are different so we need a new version.
                if common_attrs_equal:

                    # Ok, it must have been something else that changed - we need a new version
                    new_id, msg = self._add_new_version(new, session)

                # Common attrs are not equal but we still need to confirm if it's only them that differ
                else:

                    # Yes, only common attrs were different so we update in place
                    if new == existing_pd:
                        self.logger.warn(5)
                        existing_model = process_definition(session, self.request.input.cluster_id, self.request.input.id)
                        existing_model.name = new.config.name
                        existing_model.text = new.text
                        existing_model.ext_version = new.ext_version

                        session.add(existing_model)
                        session.commit()

                        msg = 'OK, updated in place'

                    # No, something got changed in addition to common attrs so we create a new version
                    else:
                        new_id, msg = self._add_new_version(new, session)

        self.response.payload.id = new_id or existing_pd.id
        self.response.payload.msg = msg

# ################################################################################################################################

class Delete(AdminService):
    __metaclass__ = DeleteMeta

# ################################################################################################################################

class Validate(AdminService):
    """ Confirms whether the definition of a process is valid or not.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_validate_request'
        response_elem = 'zato_process_definition_validate_response'
        input_required = ('text', 'lang_code')
        output_required = ('is_valid',)
        output_optional = (List('errors'), List('warnings'))

    def handle(self):
        pd = ProcessDefinition(self.request.input.lang_code)
        pd.text = self.request.input.text
        pd.parse()
        result = pd.validate()

        self.response.payload.is_valid = bool(result)
        self.response.payload.errors = [str(item) for item in result.errors]
        self.response.payload.warnings = [str(item) for item in result.warnings]

# ################################################################################################################################

class Highlight(AdminService):
    """ Turns a copy of definition into one with syntax highlighting.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_highlight_request'
        response_elem = 'zato_process_definition_highlight_response'
        input_required = ('text', 'lang_code')
        output_optional = ('highlight',)

    def handle(self):
        pd = ProcessDefinition(self.request.input.lang_code)
        pd.text = self.request.input.text
        pd.parse()
        self.response.payload.highlight = pd.highlight(self.request.input.text, self.request.input.lang_code)

# ################################################################################################################################

class GetByID(AdminService):
    """ Returns a particular process definition.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_get_by_id_request'
        response_elem = 'zato_process_definition_get_by_id_response'
        input_required = ('id',)
        output_required = ('id', 'name', 'is_active', 'version', 'created', 'created_by', 'lang_code', 'vocab_text', 'text')
        output_optional = ('ext_version', 'last_updated', 'last_updated_by')

    def get_data(self, session):
        return session.query(ProcDef).\
            filter(ProcDef.id==self.request.input.id).\
            one()

    def handle(self):
        with closing(self.odb.session()) as session:
            self.response.payload = self.get_data(session)

        self.response.payload.created = self.response.payload.created.isoformat()
        if self.response.payload.last_updated:
            self.response.payload.last_updated = self.response.payload.last_updated.isoformat()

# ################################################################################################################################
