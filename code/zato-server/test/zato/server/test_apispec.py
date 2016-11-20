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
from bunch import Bunch, bunchify

# Zato
from zato.common import API_SPEC
from zato.common.test import rand_string
from zato.server.apispec import Generator
from zato.server.apispec._docstring import Docstring, Docstring2, Docstring3
from zato.server.apispec._name import Name, Name2, Name3
from zato.server.apispec._invokes_list import InvokesList, InvokesList2, InvokesList3
from zato.server.apispec._invokes_string import InvokesString, InvokesString2, InvokesString3
from zato.server.apispec._simple_io import String, String2, String3

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

class APISpecTestCase(TestCase):

# ################################################################################################################################

    def test_name(self):
        gen = Generator(get_service_store_services(Name, Name2, Name3))
        info = gen.get_info(rand_string())

        name1 = get_dict_from_list('name', '_test.name', info)
        name2 = get_dict_from_list('name', '_test.name2', info)
        name3 = get_dict_from_list('name', '_test.name3', info)

        self.assertEquals(name1.name, '_test.name')
        self.assertEquals(name2.name, '_test.name2')
        self.assertEquals(name3.name, '_test.name3')

# ################################################################################################################################

    def test_docstring(self):
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

    def test_invokes_string(self):
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

    def test_sio_string1_open_api_v2(self):
        gen = Generator(get_service_store_services(String))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string', info)

        sio = string.simple_io[API_SPEC.OPEN_API_V2]
        sio_ireq = [sorted(elem.items()) for elem in sio.input_required]
        sio_oreq = [sorted(elem.items()) for elem in sio.output_required]

        self.assertEquals(sio.spec_name, API_SPEC.OPEN_API_V2)
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_ireq[0], [('name', 'a'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_ireq[1], [('name', 'b'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_ireq[2], [('name', 'c'), ('subtype', None), ('type', 'string')])

        self.assertEquals(sio_oreq[0], [('name', 'aa'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oreq[1], [('name', 'bb'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oreq[2], [('name', 'cc'), ('subtype', None), ('type', 'string')])

        self.assertListEqual(sio.input_optional, [])
        self.assertListEqual(sio.output_optional, [])

# ################################################################################################################################

    def test_sio_string1_zato(self):
        gen = Generator(get_service_store_services(String))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string', info)

        sio = string.simple_io['zato']
        sio_ireq = [sorted(elem.items()) for elem in sio.input_required]
        sio_oreq = [sorted(elem.items()) for elem in sio.output_required]

        self.assertEquals(sio.spec_name, 'zato')
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_ireq[0], [('name', 'a'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_ireq[1], [('name', 'b'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_ireq[2], [('name', 'c'), ('subtype', 'string'), ('type', 'string')])

        self.assertEquals(sio_oreq[0], [('name', 'aa'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oreq[1], [('name', 'bb'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oreq[2], [('name', 'cc'), ('subtype', 'string'), ('type', 'string')])

        self.assertListEqual(sio.input_optional, [])
        self.assertListEqual(sio.output_optional, [])

# ################################################################################################################################

    def test_sio_string2_open_api_v2(self):
        gen = Generator(get_service_store_services(String2))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string2', info)

        sio = string.simple_io[API_SPEC.OPEN_API_V2]
        sio_ireq = [sorted(elem.items()) for elem in sio.input_required]
        sio_iopt = [sorted(elem.items()) for elem in sio.input_optional]
        sio_oopt = [sorted(elem.items()) for elem in sio.output_optional]

        self.assertEquals(sio.spec_name, API_SPEC.OPEN_API_V2)
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_ireq[0], [('name', 'a2'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_ireq[1], [('name', 'b2'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_ireq[2], [('name', 'c2'), ('subtype', None), ('type', 'string')])

        self.assertEquals(sio_iopt[0], [('name', 'a2a'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_iopt[1], [('name', 'b2b'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_iopt[2], [('name', 'c2c'), ('subtype', None), ('type', 'string')])

        self.assertEquals(sio_oopt[0], [('name', 'aa'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oopt[1], [('name', 'bb'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oopt[2], [('name', 'cc'), ('subtype', None), ('type', 'string')])

        self.assertListEqual(sio.output_required, [])

# ################################################################################################################################

    def test_sio_string2_zato(self):
        gen = Generator(get_service_store_services(String2))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string2', info)

        sio = string.simple_io['zato']
        sio_ireq = [sorted(elem.items()) for elem in sio.input_required]
        sio_iopt = [sorted(elem.items()) for elem in sio.input_optional]
        sio_oopt = [sorted(elem.items()) for elem in sio.output_optional]

        self.assertEquals(sio.spec_name, 'zato')
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_ireq[0], [('name', 'a2'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_ireq[1], [('name', 'b2'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_ireq[2], [('name', 'c2'), ('subtype', 'string'), ('type', 'string')])

        self.assertEquals(sio_iopt[0], [('name', 'a2a'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_iopt[1], [('name', 'b2b'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_iopt[2], [('name', 'c2c'), ('subtype', 'string'), ('type', 'string')])

        self.assertEquals(sio_oopt[0], [('name', 'aa'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oopt[1], [('name', 'bb'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oopt[2], [('name', 'cc'), ('subtype', 'string'), ('type', 'string')])

        self.assertListEqual(sio.output_required, [])

# ################################################################################################################################

    def test_sio_string3_open_api_v2(self):
        gen = Generator(get_service_store_services(String3))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string3', info)

        sio = string.simple_io[API_SPEC.OPEN_API_V2]
        sio_iopt = [sorted(elem.items()) for elem in sio.input_optional]
        sio_oreq = [sorted(elem.items()) for elem in sio.output_required]
        sio_oopt = [sorted(elem.items()) for elem in sio.output_optional]

        self.assertEquals(sio.spec_name, API_SPEC.OPEN_API_V2)
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_iopt[0], [('name', 'a2a'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_iopt[1], [('name', 'b2b'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_iopt[2], [('name', 'c2c'), ('subtype', None), ('type', 'string')])

        self.assertEquals(sio_oreq[0], [('name', 'aa'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oreq[1], [('name', 'bb'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oreq[2], [('name', 'cc'), ('subtype', None), ('type', 'string')])

        self.assertEquals(sio_oopt[0], [('name', 'aaa'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oopt[1], [('name', 'bbb'), ('subtype', None), ('type', 'string')])
        self.assertEquals(sio_oopt[2], [('name', 'ccc'), ('subtype', None), ('type', 'string')])

        self.assertListEqual(sio.input_required, [])

# ################################################################################################################################

    def test_sio_string3_zato(self):
        gen = Generator(get_service_store_services(String3))
        info = gen.get_info(rand_string())
        string = get_dict_from_list('name', '_test.string3', info)

        sio = string.simple_io['zato']
        sio_iopt = [sorted(elem.items()) for elem in sio.input_optional]
        sio_oreq = [sorted(elem.items()) for elem in sio.output_required]
        sio_oopt = [sorted(elem.items()) for elem in sio.output_optional]

        self.assertEquals(sio.spec_name, 'zato')
        self.assertEquals(sio.request_elem, '')
        self.assertEquals(sio.response_elem, '')

        self.assertEquals(sio_iopt[0], [('name', 'a2a'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_iopt[1], [('name', 'b2b'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_iopt[2], [('name', 'c2c'), ('subtype', 'string'), ('type', 'string')])

        self.assertEquals(sio_oreq[0], [('name', 'aa'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oreq[1], [('name', 'bb'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oreq[2], [('name', 'cc'), ('subtype', 'string'), ('type', 'string')])

        self.assertEquals(sio_oopt[0], [('name', 'aaa'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oopt[1], [('name', 'bbb'), ('subtype', 'string'), ('type', 'string')])
        self.assertEquals(sio_oopt[2], [('name', 'ccc'), ('subtype', 'string'), ('type', 'string')])

        self.assertListEqual(sio.input_required, [])

# ################################################################################################################################
