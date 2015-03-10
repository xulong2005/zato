# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.common.broker_message import PROCESS
from zato.common.odb.model import ProcDef
from zato.common.odb.query import process_definition_list
from zato.process.definition import ProcessDefinition
from zato.server.service import List
from zato.server.service.internal import AdminService, AdminSIO
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

elem = 'process_definition'
model = ProcDef
label = 'a process definition'
broker_message = PROCESS
broker_message_prefix = 'DEFINITION_'
list_func = process_definition_list

class GetList(AdminService):
    __metaclass__ = GetListMeta

class Create(AdminService):
    __metaclass__ = CreateEditMeta

class Edit(AdminService):
    __metaclass__ = CreateEditMeta

class Delete(AdminService):
    __metaclass__ = DeleteMeta

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

class Highlight(AdminService):
    """ Turns a copy of definition into one with syntax highlighting.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_process_definition_validate_request'
        response_elem = 'zato_process_definition_validate_response'
        input_required = ('text', 'lang_code')
        output_optional = ('highlight',)

    def handle(self):
        pd = ProcessDefinition(self.request.input.lang_code)
        pd.text = self.request.input.text
        pd.parse()
        self.response.payload.highlight = pd.highlight(self.request.input.text, self.request.input.lang_code)
