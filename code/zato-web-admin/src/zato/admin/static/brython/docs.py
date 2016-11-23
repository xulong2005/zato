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

ns_tr_html_template = """
<tr id="ns-tr-{name}" class="ns-tr">
  <td id="ns-td-{name}" class="ns-td">
    <div id="ns-name-{name}" class="ns-name">{ns_name_human}</div>
    <div id="ns-options-{name}" class="ns-options">22</div>
  </td>
</tr>
"""

# ################################################################################################################################

class APISpec(object):
    """ Main object responsible for representation of API specifications.
    """
    def __init__(self, data):
        self.data = data
        self.spec_table = None

    def get_ns_tr_html(self, ns_name, ns_name_human):
        return ns_tr_html_template.format(name=ns_name, ns_name_human=ns_name_human)

    def run(self):
        # Create the main table whose individual rows are namespaces of services.
        self.spec_table = table(id='spec-table')

        for values in self.data['namespaces'].values():

            services = values['services']
            ns_docs_md = values['docs_md']
            ns_name = values['name'] or _anon_ns

            ns_tr = tr()
            ns_tr.html = self.get_ns_tr_html(ns_name, (ns_name if ns_name != _anon_ns else '(Services without a namespace)'))

            self.spec_table <= ns_tr

            '''
            ns_tr = tr(id='ns-tr-{}'.format(ns_name), class_name='ns-tr')
            ns_td = td(id='ns-td-{}'.format(ns_name), class_name='ns-td')

            ns_div_name = div(id='ns-div-name-{}'.format(ns_name), class_name='ns-div-name')
            ns_div_options = div(id='ns-div-options-{}'.format(ns_name), class_name='ns-div-options')

            ns_div_name <= (ns_name if ns_name != _anon_ns else '(Services without a namespace)')
            ns_div_options.html = '<a href="zzz">aaa</a>'

            ns_td <= ns_div_name
            ns_td <= ns_div_options
            ns_tr <= ns_td
            '''

        doc['main-div'] <= self.spec_table

        '''
            for service in services:
                print(service)
                '''

        #print(self.data)

# ################################################################################################################################

apispec = APISpec(loads(doc['docs-data'].text))
apispec.run()

# ################################################################################################################################
