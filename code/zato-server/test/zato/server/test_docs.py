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
from zato.server.docs._docstring import Docstring, Docstring2, Docstring3
from zato.server.docs._name import Name, Name2, Name3
from zato.server.docs._invokes_list import InvokesList, InvokesList2, InvokesList3
from zato.server.docs._invokes_string import InvokesString, InvokesString2, InvokesString3
from zato.server.docs._simple_io import String, String2, String3

logger = getLogger(__name__)

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

    def xtest_name(self):
        gen = Generator(get_service_store_services(Name, Name2, Name3))
        info = gen.get_info(rand_string())

        name1 = get_dict_from_list('name', '_test.name', info)
        name2 = get_dict_from_list('name', '_test.name2', info)
        name3 = get_dict_from_list('name', '_test.name3', info)

        self.assertEquals(name1.name, '_test.name')
        self.assertEquals(name2.name, '_test.name2')
        self.assertEquals(name3.name, '_test.name3')

# ################################################################################################################################

    def xtest_docstring(self):
        gen = Generator(get_service_store_services(Docstring, Docstring2, Docstring3))
        info = gen.get_info(rand_string())

        docstring1 = get_dict_from_list('name', '_test.docstring', info)
        docstring2 = get_dict_from_list('name', '_test.docstring2', info)
        docstring3 = get_dict_from_list('name', '_test.docstring3', info)

        self.assertEquals(docstring1.name, '_test.docstring')
        self.assertEquals(docstring1.docs.summary, 'Docstring Summary')
        self.assertEquals(docstring1.docs.description, '')
        self.assertEquals(docstring1.docs.full, 'Docstring Summary')

        self.assertEquals(docstring2.name, '_test.docstring2')
        self.assertEquals(docstring2.docs.summary, 'Docstring2 Summary')
        self.assertEquals(docstring2.docs.description, 'Docstring2 Description')
        self.assertEquals(docstring2.docs.full, 'Docstring2 Summary.\n\nDocstring2 Description')

        self.assertEquals(docstring3.name, '_test.docstring3')
        self.assertEquals(docstring3.docs.summary, 'Docstring3 Summary')
        self.assertEquals(docstring3.docs.description, 'Docstring3 Description\n\nDocstring3 Description2')
        self.assertEquals(docstring3.docs.full, 'Docstring3 Summary.\n\nDocstring3 Description\n\nDocstring3 Description2')

# ################################################################################################################################

    def xtest_invokes_string(self):
        gen = Generator(get_service_store_services(InvokesString, InvokesString2, InvokesString3))
        info = gen.get_info(rand_string())

        invokes_string1 = get_dict_from_list('name', '_test.invokes-string', info)
        invokes_string2 = get_dict_from_list('name', '_test.invokes-string2', info)
        invokes_string3 = get_dict_from_list('name', '_test.invokes-string3', info)

        self.assertEquals(invokes_string1.name, '_test.invokes-string')
        self.assertListEqual(invokes_string1.invokes, ['_test.invokes-string2'])
        self.assertListEqual(invokes_string1.invoked_by, [])

        self.assertEquals(invokes_string2.name, '_test.invokes-string2')
        self.assertListEqual(invokes_string2.invokes, ['_test.invokes-string3'])
        self.assertListEqual(invokes_string2.invoked_by, ['_test.invokes-string', '_test.invokes-string3'])

        self.assertEquals(invokes_string3.name, '_test.invokes-string3')
        self.assertListEqual(invokes_string3.invokes, ['_test.invokes-string2'])
        self.assertListEqual(invokes_string3.invoked_by, ['_test.invokes-string2'])

# ################################################################################################################################

    def xtest_invokes_list(self):
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

    def test_sio_string(self):
        gen = Generator(get_service_store_services(String, String2, String3))
        info = gen.get_info(rand_string())

        string1 = get_dict_from_list('name', '_test.string', info)
        string2 = get_dict_from_list('name', '_test.string2', info)
        string3 = get_dict_from_list('name', '_test.string3', info)

# ################################################################################################################################
