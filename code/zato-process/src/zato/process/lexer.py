# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import re

# Pygments
from pygments import highlight
from pygments import token as tok
from pygments.formatters import HtmlFormatter, Terminal256Formatter
from pygments.lexer import Lexer, RegexLexer

class ProcessDefinitionLexer(RegexLexer):
    name = 'Zato Process'
    aliases = ['zato-proc']
    filenames = ['*.zato-proc']
    flags = re.MULTILINE | re.DOTALL

    def __init__(self, zato_vocab, *args, **kwargs):
        super(ProcessDefinitionLexer, self).__init__(*args, **kwargs)
        self.zato_vocab = zato_vocab

    tokens = {
       b'root': [
           (r'(Config:|Path:|Handler:|Pipeline:|'
            r'Name:|Start:|from|Map service|to|str|int|list|dict|'
            r'Require|else|Wait for signal|Wait for signals|on timeout|'
            r'If|Else|Set|Emit|'
            r'enter|invoke|Enter|Invoke|Fork to|under|and wait)', tok.Keyword),
       ],
   }

if __name__ == '__main__':
    proc = """Config:

  Name: My process
  Start: order.management from my.channel.feasibility-study

  Map service adapter.crm.delete.user to delete.crm
  Map service adapter.billing.delete.user to delete.billing

Pipeline:
  user_name: str
  user_id: int
  user_addresses: list
  user_social: dict

Path: order.management

  Require feasibility.study else reject.order
  Enter order.complete
  Require abc.def

  Wait for signal patch.complete
  Wait for signal signal.name on timeout 30s enter path.name
  Wait for signal signal.name on timeout 60m invoke service.name

  Wait for signals patch.complete, patch.drop
  Wait for signals signal.name on timeout 30s enter path.name
  Wait for signals signal.name on timeout 60m invoke service.name

  Invoke service.name

  Fork to path1, path2 under my.fork and wait
  Fork to path1, path2

  If my.condition invoke my.service
  Else invoke my.service2

  If my.condition enter my.path
  Else invoke my.path2

  Emit my.event
  Set my.key = my.value

Handler: cease

  Require feasibility.study else reject.order
  Enter order.complete
  Require abc.def

  Wait for signal patch.complete
  Wait for signal signal.name on timeout 30s enter path.name
  Wait for signal signal.name on timeout 60m invoke service.name

  Wait for signals patch.complete, patch.drop
  Wait for signals signal.name on timeout 30s enter path.name
  Wait for signals signal.name on timeout 60m invoke service.name

  Invoke service.name

  Fork to path1, path2 under my.fork and wait
  Fork to path1, path2

  If my.condition invoke my.service
  Else invoke my.service2

  If my.condition enter my.path
  Else invoke my.path2

  Emit my.event
  Set my.key = my.value

Handler: amend
  Invoke core.order.amend

Handler: patch.complete
  Invoke core.order.patch-complete

Handler: drop.complete
  Invoke core.order.on-drop-complete

Path: feasibility.study
  Invoke core.order.feasibility-study

Path: order.complete
  Invoke core.order.notify-complete

Path: reject.order
  Invoke core.order.reject
  Emit order.rejected""".strip()

source_html = highlight(proc, ProcessDefinitionLexer('zz',stripnl=False), Terminal256Formatter(linenos='table'))
print(source_html)
