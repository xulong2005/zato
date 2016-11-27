# -*- coding: utf-8 -*-

"""
Copyright (C) 2016, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from json import loads

# Brython
from browser import document as doc, window
from browser.html import A as a, DIV as div, TABLE as table, TR as tr, TD as td

# ################################################################################################################################

_anon_ns = 'zato_anonymous'

# ################################################################################################################################

# Taken from https://docs.python.org/3.3/library/itertools.html#itertools.zip_longest

class ZipExhausted(Exception):
    pass

def chain(*iterables):
    """ chain('ABC', 'DEF') --> A B C D E F
    """
    for it in iterables:
        for element in it:
            yield element

def repeat(object, times=None):
    """ repeat(10, 3) --> 10 10 10
    """
    if times is None:
        while True:
            yield object
    else:
        for i in range(times):
            yield object

def zip_longest(*args, **kwds):
    """ zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    """
    fillvalue = kwds.get('fillvalue')
    counter = len(args) - 1
    def sentinel():
        nonlocal counter
        if not counter:
            raise ZipExhausted
        counter -= 1
        yield fillvalue
    fillers = repeat(fillvalue)
    iterators = [chain(it, sentinel(), fillers) for it in args]
    try:
        while iterators:
            yield tuple(map(next, iterators))
    except ZipExhausted:
        pass

# ################################################################################################################################

tr_ns_html_contents_template = """
<td id="td-ns-{name}" class="td-ns">
  <div id="ns-name-{name}" class="ns-name">{ns_name_human} <span class="docs">{ns_docs_md}</span></div>
  <div id="ns-options-{name}" class="ns-options"><a href="#">Toggle services</a> | <a href="#">Toggle all details</a></div>
</td>
"""

tr_service_html_contents_template = """
<td id="td-service-{name}" class="td-service">
  <div id="service-name-{name}" class="service-name">{service_no}. {name} <span class="service-desc" id="service-desc-{name}"></span></div>
  <div id="service-options-{name}" class="service-options"><a href="#">Toggle details</a></div>
  <div class="service-details">
    <span class="header">
      <a href="#" id="service-header-docs-{name}">Docs</a>
      |
      <a href="#" id="service-header-deps-{name}">Dependencies</a>
      |
      <a href="#" id="service-header-io-{name}">I/O</a>
    </span>
  </div>
  <div id="service-details-deps-{name}" class="current-details zhidden">Dependencies</div>
  <div id="service-details-io-{name}" class="current-details zhidden">I/O</div>
  <div id="service-details-docs-{name}" class="current-details visible"/>
</td>
"""

deps_template = """
<p>Invokes: {invokes}</p>
<p>Invoked by: {invoked_by}</p>
"""

io_template = """
<table>
  <thead>
    <tr>
      <th colspan="2">Input</th>
      <th colspan="2">Output</th>
    </tr>
  </thead>
  <tbody id="io-tbody-{name}">
  </tbody>
</table>
"""

io_row_template = """
    <tr>
      <td class="io-name">{input_name}</td>
      <td class="io-data-type">{input_data_type}</td>
      <td class="io-name">{output_name}</td>
      <td class="io-data-type">{output_data_type}</td>
    </tr>
"""

none_html = '<span class="form_hint">(None)</span>'

# ################################################################################################################################

class APISpec(object):
    """ Main object responsible for representation of API specifications.
    """
    def __init__(self, data):
        self.data = data
        self.spec_table = table(id='spec-table')
        self.cluster_id = doc['cluster_id'].value

    def get_tr_ns_html(self, ns_name, ns_name_human, ns_docs_md=''):
        return tr_ns_html_contents_template.format(name=ns_name, ns_name_human=ns_name_human, ns_docs_md=ns_docs_md)

    def _get_deps(self, deps):
        out = []
        for name in deps:
            out.append('<a href="/zato/service/overview/{name}/?cluster={cluster_id}">{name}</a>'.format(
                name=name, cluster_id=self.cluster_id))

        return ', '.join(out) or none_html

    def get_deps_html(self, invokes, invoked_by):
        return deps_template.format(invokes=self._get_deps(invokes), invoked_by=self._get_deps(invoked_by))

    def get_io_html(self, name, io):
        if not io:
            return none_html

        _input = io['input_required'] + io['input_optional']
        _output = io['output_required'] + io['output_optional']

        for elems in zip_longest(_input, _output):
            _input_elem, _output_elem = elems
            print(_input_elem, _output_elem)
        print()

        return io_template.format(name=name)

    def get_tr_service_html(self, service_no, service):
        name = service['name']
        return tr_service_html_contents_template.format(name=name, service_no=service_no)

    def run(self):
        """ Creates a table with all the namespaces and services.
        """
        default_ns_name_human = '<span class="form_hint" style="font-size:100%;font-style:italic">(Services without a namespace)</span>'

        # Maps names of services to their summaries and descriptions
        service_details = {}

        for values in self.data['namespaces'].values():

            # Config
            services = values['services']
            ns_docs_md = values['docs_md']
            ns_name = values['name'] or _anon_ns

            # Create a new row for each namespace
            tr_ns = tr(id='tr-ns-{}'.format(ns_name))
            tr_ns.class_name='tr-ns'
            tr_ns.html = self.get_tr_ns_html(
                ns_name, (ns_name if ns_name != _anon_ns else default_ns_name_human), ns_docs_md)

            # Append namespaces to the main table
            self.spec_table <= tr_ns

            # Append a row for each service in a given namespace
            for idx, service in enumerate(services):
                tr_service = tr(id='tr-service-{}'.format(service['name']))
                tr_service.class_name='tr-service'
                tr_service.html = self.get_tr_service_html(idx+1, service)
                self.spec_table <= tr_service
                service_details[service['name']] = {

                    'docs': {
                        'summary': service['docs']['summary_html'],
                        'full': service['docs']['full_html'],
                    },

                    'deps': {
                        'invokes': service['invokes'],
                        'invoked_by': service['invoked_by']
                    },

                    'io': service['simple_io'].get('zato', {})

                }

        # We can append the table with contents to the main div
        doc['main-div'] <= self.spec_table

        # Now we can set up details by their div IDs
        for name, details in service_details.items():

            docs = details['docs']
            doc['service-desc-{}'.format(name)].html = docs['summary']
            doc['service-details-docs-{}'.format(name)].html = docs['full']

            deps = details['deps']
            doc['service-details-deps-{}'.format(name)].html = self.get_deps_html(deps['invokes'], deps['invoked_by'])

            io = details['io']
            doc['service-details-io-{}'.format(name)].html = self.get_io_html(name, io)

# ################################################################################################################################

apispec = APISpec(loads(doc['docs-data'].text))
apispec.run()

# ################################################################################################################################
