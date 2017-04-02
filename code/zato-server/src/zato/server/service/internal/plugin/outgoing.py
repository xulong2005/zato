# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from contextlib import closing
from traceback import format_exc

# Zato
from zato.server.service import AsIs
from zato.server.service.internal import AdminService, GetListAdminSIO

class GetList(AdminService):
    """ Returns a list of outgoing plugin definitions.
    """
    _filter_by = 'name',

    class SimpleIO(GetListAdminSIO):
        request_elem = 'zato_outgoing_zmq_get_list_request'
        response_elem = 'zato_outgoing_zmq_get_list_response'
        input_required = ('cluster_id',)
        output_required = (AsIs('id'), 'transport', 'name', 'is_active', 'is_internal',  'py_name', 'version', 'author', 'homepage',
            'file_name', 'repo_revision')

    def handle(self):
        response = [
            {
              'id': 1,
              'transport': 'HTTP',
              'name': 'CouchDB',
              'is_active': True,
              'is_internal': False,
              'py_name': 'couchdb',
              'version': '1',
              'author': 'Foo Bar',
              'homepage': 'https://example.com',
              'file_name': 'couchdb.ini',
              'repo_revision': 'e763cba'
            },
        ]

        self.response.payload[:] = response
