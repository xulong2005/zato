# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.admin.web.views import CreateEdit, Delete as _Delete, Index as _Index, method_allowed

# ################################################################################################################################

attrs = ('id', 'transport', 'name', 'is_active', 'is_internal', 'version', 'author', 'homepage', 'py_name', 'file_name',
    'repo_revision')

# ################################################################################################################################

class Plugin(object):
    __slots__ = attrs

# ################################################################################################################################

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'plugin-outgoing'
    template = 'zato/plugin/outgoing/index.html'
    service_name = 'zato.plugin.outgoing.get-list'
    output_class = Plugin
    paginate = True

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        input_optional = ('query',)
        output_required = attrs
        output_repeated = True

    def handle(self):
        return {}

# ################################################################################################################################

@method_allowed('GET')
def create(req, cluster_id):
    """ Returns a form to create new plugins.
    """

# ################################################################################################################################

@method_allowed('GET')
def edit(req, cluster_id, plugin_id):
    """ Returns a form to edit an existing plugin.
    """

# ################################################################################################################################

@method_allowed('GET')
def install(req, cluster_id):
    """ Returns a form to install plugins from files or remote servers.
    """

# ################################################################################################################################
