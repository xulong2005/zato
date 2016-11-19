# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from logging import getLogger
from pprint import pprint
from unittest import TestCase

# Bunch
from bunch import bunchify

# Zato
from zato.common.test import rand_string
from zato.server.docs import Generator
from zato.server.docs._invokes_list import InvokesList, InvokesList2, InvokesList3
from zato.server.docs._invokes_string import InvokesString, InvokesString2, InvokesString3

logger = getLogger(__name__)

from zato.server.service import Service

# ################################################################################################################################

def get_service_store_services(*service_classes):
    out = {}
    for service_class in service_classes:
        out[service_class.get_impl_name()] = {'name':service_class.get_name(), 'service_class':service_class}
    return out

# ################################################################################################################################

def get_dict_from_list(key, value, list_, as_bunch=True):
    for dict_ in list_:
        if dict_.get(key) == value:
            return bunchify(dict_) if as_bunch else dict_
    else:
        raise ValueError('No such key/value {}/{} in {}'.format(key, value, list_))

# ################################################################################################################################

class DocsTestCase(TestCase):

# ################################################################################################################################

    def test_name(self):
        gen = Generator(get_service_store_services(InvokesString, InvokesString2, InvokesString3))
        info = gen.get_info(rand_string())

        invokes_string1 = get_dict_from_list('name', '_test.invokes-string', info)
        invokes_string2 = get_dict_from_list('name', '_test.invokes-string2', info)
        invokes_string3 = get_dict_from_list('name', '_test.invokes-string3', info)

        self.assertEquals(invokes_string1.name, '_test.invokes-string')
        self.assertEquals(invokes_string2.name, '_test.invokes-string2')
        self.assertEquals(invokes_string3.name, '_test.invokes-string3')

# ################################################################################################################################

    def test_docstring(self):
        gen = Generator(get_service_store_services(InvokesString, InvokesString2, InvokesString3))
        info = gen.get_info(rand_string())

        invokes_string1 = get_dict_from_list('name', '_test.invokes-string', info)
        invokes_string2 = get_dict_from_list('name', '_test.invokes-string2', info)
        invokes_string3 = get_dict_from_list('name', '_test.invokes-string3', info)

        self.assertEquals(invokes_string1.name, '_test.invokes-string')
        self.assertEquals(invokes_string1.docs.summary, 'InvokesString Summary')
        self.assertEquals(invokes_string1.docs.description, '')
        self.assertEquals(invokes_string1.docs.full, 'InvokesString Summary')

        self.assertEquals(invokes_string2.name, '_test.invokes-string2')
        self.assertEquals(invokes_string2.docs.summary, 'InvokesString2 Summary')
        self.assertEquals(invokes_string2.docs.description, 'InvokesString2 Description')
        self.assertEquals(invokes_string2.docs.full, 'InvokesString2 Summary.\n\nInvokesString2 Description')

        self.assertEquals(invokes_string3.name, '_test.invokes-string3')
        self.assertEquals(invokes_string3.docs.summary, 'InvokesString3 Summary')
        self.assertEquals(invokes_string3.docs.description, 'InvokesString3 Description\n\nInvokesString3 Description2')
        self.assertEquals(invokes_string3.docs.full, 'InvokesString3 Summary.\n\nInvokesString3 Description\n\nInvokesString3 Description2')

# ################################################################################################################################

    def test_invokes_list(self):
        gen = Generator(get_service_store_services(InvokesList, InvokesList2, InvokesList3))
        info = gen.get_info(rand_string())

        invokes_list1 = get_dict_from_list('name', '_test.invokes-list', info)
        invokes_list2 = get_dict_from_list('name', '_test.invokes-list2', info)
        invokes_list3 = get_dict_from_list('name', '_test.invokes-list3', info)

        self.assertEquals(invokes_list1.name, '_test.invokes-list')
        self.assertListEqual(invokes_list1.invokes, ['_test.invokes-list2', '_test.invokes-list3'])
        self.assertListEqual(invokes_list1.invoked_by, [])

        self.assertEquals(invokes_list2.name, '_test.invokes-list2')
        self.assertListEqual(invokes_list2.invokes, ['_test.invokes-list3'])
        self.assertListEqual(invokes_list2.invoked_by, ['_test.invokes-list', '_test.invokes-list3'])

        self.assertEquals(invokes_list3.name, '_test.invokes-list3')
        self.assertListEqual(invokes_list3.invokes, ['_test.invokes-list2'])
        self.assertListEqual(invokes_list3.invoked_by, ['_test.invokes-list', '_test.invokes-list2'])

# ################################################################################################################################
