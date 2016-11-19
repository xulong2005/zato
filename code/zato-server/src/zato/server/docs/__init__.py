# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from inspect import getmodule

# Bunch
from bunch import Bunch, bunchify

# docformatter
from docformatter import format_docstring, split_summary_and_description as split_docstring

_sio_attrs = ('input_required', 'output_required', 'input_optional', 'output_optional', 'request_elem', 'response_elem')
_service_attrs = ('namespace', 'all')

# ################################################################################################################################

class Config(object):
    def __init__(self):
        self.is_module_level = True
        self.ns = ''
        self.services = []

# ################################################################################################################################

class Docstring(object):
    def __init__(self):
        self.summary = ''
        self.description = ''
        self.full = ''

# ################################################################################################################################

class SimpleIO(object):
    def __init__(self):
        self.input_required = []
        self.output_required = []
        self.input_optional = []
        self.output_optional = []
        self.request_elem = ''
        self.response_elem = ''

# ################################################################################################################################

class ServiceInfo(object):
    """ Contains information about a service basing on which documentation is generated.
    """
    def __init__(self, name, service_class):
        self.name = name
        self.service_class = service_class
        self.config = Config()
        self.simple_io = SimpleIO()
        self.docstring = Docstring()
        self.invokes = []
        self.invoked_by = []
        self.parse()

# ################################################################################################################################

    def parse(self):
        self.set_config()
        self.set_simple_io()
        self.set_summary_desc()

# ################################################################################################################################

    def _add_services_from_invokes(self):
        """
        class MyService(Service):
          invokes = 'foo'

        class MyService(Service):
          invokes = ['foo', 'bar']
        """
        invokes = getattr(self.service_class, 'invokes', None)
        if invokes:
            if isinstance(invokes, basestring):
                self.invokes.append(invokes)
            else:
                if isinstance(invokes, (list, tuple)):
                    self.invokes.extend(list(invokes))

# ################################################################################################################################

    def set_config(self):
        self._add_services_from_invokes()

        '''
        service_config = getattr(self.service_class, 'Config', None)
        module_config = getattr(getmodule(self.service_class), 'Config', None)

        if service_config:
            _service = getattr(service_config, 'Service')
            if _service:
                print()
                for name in dir(_service):

                    if name.startswith('__'):
                        continue

                    if name in _service_attrs:
                        continue

                    service = getattr(_service, name)
                    print(33, name, service)

        #print(33, service_config)
        #print(44, module_config)
        '''

# ################################################################################################################################

    def set_simple_io(self):

        simple_io = getattr(self.service_class, 'SimpleIO', None)

        if simple_io:
            for attr in _sio_attrs:
                value = getattr(simple_io, attr, None)
                if value:
                    setattr(self.simple_io, attr, value)

# ################################################################################################################################

    def set_summary_desc(self):

        doc = self.service_class.__doc__
        if not doc:
            return

        split = doc.splitlines()
        summary = split[0]

        # format_docstring expects an empty line between summary and description
        if len(split) > 1:
            _doc = []
            _doc.append(split[0])
            _doc.append('')
            _doc.extend(split[1:])
            doc = '\n'.join(_doc)

        # This gives us the full docstring out of which we need to extract description alone.
        full_docstring = format_docstring('', '"{}"'.format(doc), post_description_blank=False)
        full_docstring = full_docstring.lstrip('"""').rstrip('"""')
        description = full_docstring.splitlines()

        # If there are multiple lines and the second one is empty this means it is an indicator of a summary to follow.
        if len(description) > 1 and not description[1]:
            description = '\n'.join(description[2:])
        else:
            description = ''

        # docformatter.normalize_summary adds superfluous period at end docstring.
        if full_docstring:
            if description and full_docstring[-1] == '.' and full_docstring[-1] != description[-1]:
                full_docstring = full_docstring[:-1]

            if summary and full_docstring[-1] == '.' and full_docstring[-1] != summary[-1]:
                full_docstring = full_docstring[:-1]

        self.docstring.summary = summary.strip()
        self.docstring.description = description
        self.docstring.full = full_docstring.rstrip()

# ################################################################################################################################

class Generator(object):
    def __init__(self, service_store_services):
        self.service_store_services = service_store_services
        self.services = {}

        # Service name -> list of services this service invokes
        self.invokes = {}

        # Service name -> list of services this service is invoked by
        self.invoked_by = {}

    def get_info(self, ignore_prefix='zato'):
        """ Returns a list of dicts containing metadata about services in the scope required to generate docs and API clients.
        """
        self.parse(ignore_prefix)
        out = []

        for name in sorted(self.services):
            info = self.services[name]
            item = Bunch()

            item.name = info.name
            item.docs = Bunch()
            item.docs.summary = info.docstring.summary
            item.docs.description = info.docstring.description
            item.docs.full = info.docstring.full
            item.invokes = info.invokes
            item.invoked_by = info.invoked_by

            out.append(item.toDict())

        return out

# ################################################################################################################################

    def parse(self, ignore_prefix):

        for impl_name, details in self.service_store_services.iteritems():
            if not impl_name.startswith(ignore_prefix):
                details = bunchify(details)
                info = ServiceInfo(details['name'], details['service_class'])
                self.services[info.name] = info

        for name, info in self.services.iteritems():
            self.invokes[name] = info.invokes

        for source, targets in self.invokes.iteritems():
            for target in targets:
                sources = self.invoked_by.setdefault(target, [])
                sources.append(source)

        for name, info in self.services.iteritems():
            info.invoked_by = self.invoked_by.get(name, [])

# ################################################################################################################################
