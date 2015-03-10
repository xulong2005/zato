# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import re

from pygments import token as tok
from pygments.lexer import RegexLexer

class ProcessDefinitionLexer(RegexLexer):
    name = 'Zato Process'
    aliases = ['zato-proc']
    filenames = ['*.zato-proc']
    flags = re.MULTILINE | re.DOTALL

class ProcessDefinitionLexer_en_uk(ProcessDefinitionLexer):

    tokens = {
       b'root': [
           (r'(Config:|Path:|Handler:|Pipeline:|'
            r'Name:|Start:|from|Map service|to|str|int|list|dict|'
            r'Require|else|Wait for signal|Wait for signals|on timeout|'
            r'If|Else|Set|Emit|'
            r'enter|invoke|Enter|Invoke|Fork to|under|and wait)', tok.Keyword),
       ],
   }

lexer_dict = {
    'en_uk': ProcessDefinitionLexer_en_uk
}
