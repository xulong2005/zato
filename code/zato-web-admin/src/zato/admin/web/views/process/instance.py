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
from zato.admin.web.views import Index as _Index
from zato.common.odb.model import ProcInst

logger = logging.getLogger(__name__)

# ################################################################################################################################

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'process-instance'
    template = 'zato/process/instance/index.html'
    service_name = 'proc.get-instances'
    output_class = ProcInst

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('id', 'process_id', 'created', 'last_updated')
        output_repeated = True

    def handle(self):
        return {}
