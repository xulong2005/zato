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
    <div class="invokes-invoked-sio">
    <div class="sample"></div>
  </div>
</td>
"""

# ################################################################################################################################

class APISpec(object):
    """ Main object responsible for representation of API specifications.
    """
    def __init__(self, data):
        self.data = data
        self.spec_table = table(id='spec-table')

    def get_tr_ns_html(self, ns_name, ns_name_human, ns_docs_md=''):
        return tr_ns_html_contents_template.format(name=ns_name, ns_name_human=ns_name_human, ns_docs_md=ns_docs_md)

    def get_tr_service_html(self, service_no, service):
        print(service)
        name = service['name']
        return tr_service_html_contents_template.format(name=name, service_no=service_no)

    def run(self):
        """ Creates a table with all the namespaces and services.
        """
        default_ns_name_human = '<span class="form_hint" style="font-size:100%;font-style:italic">(Services without a namespace)</span>'

        # Maps names of services to their summaries and descriptions
        service_docs = {}

        for values in self.data['namespaces'].values():

            # Config
            services = values['services']
            ns_docs_md = values['docs_md']
            ns_name = values['name'] or _anon_ns

            # Create a new row for each namespace
            tr_ns = tr(id='tr-ns-{}'.format(ns_name), class_name='tr-ns')
            tr_ns.html = self.get_tr_ns_html(
                ns_name, (ns_name if ns_name != _anon_ns else default_ns_name_human), ns_docs_md)

            # Append namespaces to the main table
            self.spec_table <= tr_ns

            # Append a row for each service in a given namespace
            for idx, service in enumerate(services):
                tr_service = tr(id='tr-service-{}'.format(service['name']), class_name='tr-service')
                tr_service.html = self.get_tr_service_html(idx+1, service)
                self.spec_table <= tr_service
                service_docs[service['name']] = {
                    'summary': service['docs']['summary_html'],
                    'desc': service['docs']['description_html'],
                }

        # We can append the table with contents to the main div
        doc['main-div'] <= self.spec_table

        # Now we can set up documentation
        for name, docs in service_docs.items():
            doc['service-desc-{}'.format(name)].html = docs['summary']
            print(name, docs)

# ################################################################################################################################

apispec = APISpec(loads(doc['docs-data'].text))
apispec.run()

# ################################################################################################################################
