# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from httplib import OK
from json import dumps, loads
from traceback import format_exc

# Django
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.template.response import TemplateResponse

# Zato
from zato.admin.web.forms.process.definition import CreateForm, EditForm
from zato.admin.web.views import CreateEdit, Delete as _Delete, error_from_zato_env, Index as _Index
from zato.common.odb.model import ProcDef
from zato.common.util import current_host, get_current_user

logger = logging.getLogger(__name__)

common_post = ('lang_code', 'text')

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'process-definition'
    template = 'zato/process/definition/index.html'
    service_name = 'zato.process.definition.get-list'
    output_class = ProcDef

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('id', 'name', 'is_active', 'lang_code', 'text', 'version')
        output_repeated = True

    def handle(self):
        return {}

class _CreateEdit(CreateEdit):
    method_allowed = 'POST'

    class SimpleIO(CreateEdit.SimpleIO):
        input_required = ('name', 'is_active', 'lang_code', 'text')
        output_required = ('id', 'name')

    def success_message(self, item):
        return 'Successfully {0} the connection [{1}]'.format(self.verb, item.name)

def create(req, cluster_id):
    return_data = {
        'cluster_id':cluster_id,
        'created_by': '{} ({})'.format(req.user, '{}@{}'.format(get_current_user(), current_host())),
        'zato_clusters':req.zato.clusters,
        'create_form': CreateForm()
    }
    return TemplateResponse(req, 'zato/process/definition/create.html', return_data)

def edit(req, cluster_id):
    return ''

def _validate_save(req, cluster_id, service_suffix, error_msg, success_msg, *args):

    try:
        response = req.zato.client.invoke_from_post('zato.process.definition.{}'.format(service_suffix), *args)
    except Exception, e:
        return error_from_zato_env(e, error_msg)
    else:
        return HttpResponse(success_msg) if response.data.is_valid else HttpResponseBadRequest(
            ('\n'.join(response.data.errors) + '\n' + '\n'.join(response.data.warnings)).strip())

def validate(req, cluster_id):
    return _validate_save(
        req, cluster_id, 'validate', 'Could not validate the definition', 'OK, validated', *common_post)

def validate_save(req, cluster_id):

    # First, validate
    result = validate(req, cluster_id)

    # Bail out if the definition wasn't valid at all
    if result.status_code != OK:
        return result

    # Now attempt to actually create it
    try:
        response = req.zato.client.invoke_from_post(
            'zato.process.definition.create', *(common_post + ('name', 'cluster_id', 'created_by')))
    except Exception, e:
        return error_from_zato_env(e, error_msg)
    else:
        return HttpResponse('OK, validated and saved')

def highlight(req, cluster_id):

    try:
        response = req.zato.client.invoke_from_post('zato.process.definition.highlight', *common_post)
    except Exception, e:
        return error_from_zato_env(e, 'Could not highlight the definition')
    else:
        return HttpResponse(response.data.highlight)

def submit(req, cluster_id):
    return {
        'validate': validate,
        'validate_save': validate_save,
        'toggle_highlight': highlight
    }[req.POST['action']](req, cluster_id)

class Delete(_Delete):
    url_name = 'process-definition-delete'
    error_message = 'Could not delete the definition'
    service_name = 'zato.process.definition.delete'
