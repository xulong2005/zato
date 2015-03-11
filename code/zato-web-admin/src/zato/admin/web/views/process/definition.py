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
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import redirect
from django.template.response import TemplateResponse

# Zato
from zato.admin.web.forms.process.definition import CreateForm, EditForm
from zato.admin.web.views import CreateEdit, Delete as _Delete, error_from_zato_env, Index as _Index
from zato.common.odb.model import ProcDef
from zato.common.util import current_host, get_current_user

logger = logging.getLogger(__name__)

common_post = ('lang_code', 'text')

# We keep this pass-through level of indirection
# so that the service to be invoked is not taken
# directly from user.
func_types = {
    'create': 'create',
    'edit': 'edit',
}

# ################################################################################################################################

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'process-definition'
    template = 'zato/process/definition/index.html'
    service_name = 'zato.process.definition.get-list'
    output_class = ProcDef

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('id', 'name', 'is_active', 'lang_code', 'text', 'version')
        output_optional = ('ext_version',)
        output_repeated = True

    def handle(self):
        return {}

# ################################################################################################################################

def _create_edit(req, cluster_id, is_create=True, process_id=None):

    extra_data = {}

    if is_create:
        user = 'created_by'
        form_name, form = 'create_form', CreateForm()
    else:
        user = 'last_updated_by'
        form_name = 'edit_form'

        response = req.zato.client.invoke('zato.process.definition.get-by-id', {'id':process_id})

        extra_data['version'] = response.data.get('version', '')
        extra_data['msg'] = req.GET.get('msg', '')
        extra_data['id'] = process_id

        form = EditForm(post_data=response.data)

    return_data = {
        'cluster_id':cluster_id,
        user: '{} ({})'.format(req.user, '{}@{}'.format(get_current_user(), current_host())),
        'zato_clusters':req.zato.clusters,
        form_name: form,
    }

    return_data.update(extra_data)

    return TemplateResponse(req, 'zato/process/definition/{}.html'.format('create' if is_create else 'edit'), return_data)

def create(req, cluster_id):
    return _create_edit(req, cluster_id, True)

def edit(req, cluster_id, process_id):
    return _create_edit(req, cluster_id, False, process_id)

# ################################################################################################################################

def _validate_save(req, cluster_id, service_suffix, success_msg, error_msg, *args):

    try:
        response = req.zato.client.invoke_from_post('zato.process.definition.{}'.format(service_suffix), *args)
    except Exception, e:
        return error_from_zato_env(e, error_msg)
    else:
        return HttpResponse(success_msg) if response.data.is_valid else HttpResponseBadRequest(
            ('\n'.join(response.data.errors) + '\n' + '\n'.join(response.data.warnings)).strip())

# ################################################################################################################################

def validate(req, cluster_id):
    return _validate_save(
        req, cluster_id, 'validate', 'OK, validated', 'Could not validate the definition', *common_post)

# ################################################################################################################################

def validate_save(req, cluster_id):

    # First, validate
    result = validate(req, cluster_id)

    # Bail out if the definition wasn't valid at all
    if result.status_code != OK:
        return result

    # Now attempt to actually create it
    try:
        response = req.zato.client.invoke_from_post(
            'zato.process.definition.{}'.format(func_types[req.POST['func_type']]),
            *(common_post + ('id', 'name', 'cluster_id', 'created_by', 'last_updated_by', 'ext_version')))
    except Exception, e:
        return error_from_zato_env(e, error_msg)
    else:
        redirect_to = reverse('process-definition-edit', args=(cluster_id, response.data.id))
        redirect_to += '?msg={}'.format(response.data.msg)
        return HttpResponse(redirect_to)

# ################################################################################################################################

def highlight(req, cluster_id):

    try:
        response = req.zato.client.invoke_from_post('zato.process.definition.highlight', *common_post)
    except Exception, e:
        return error_from_zato_env(e, 'Could not highlight the definition')
    else:
        return HttpResponse(response.data.highlight)

# ################################################################################################################################

def submit(req, cluster_id):
    return {
        'validate': validate,
        'validate_save': validate_save,
        'toggle_highlight': highlight
    }[req.POST['action']](req, cluster_id)

# ################################################################################################################################

class Delete(_Delete):
    url_name = 'process-definition-delete'
    error_message = 'Could not delete the definition'
    service_name = 'zato.process.definition.delete'

# ################################################################################################################################
