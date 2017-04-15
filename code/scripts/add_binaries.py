# -*- coding: utf-8 -*-

"""
Copyright (C) 2017, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os
import sys

# ###############################################################################################################################

template = """#!{executable}

import sys
sys.path[0:0] = [
  {sys_path}
]

{binary_specific}
"""

# ###############################################################################################################################

def get_sys_path():

    out = []
    for item in sorted(sys.path):
        out.append("'{}'".format(item))

    return out

# ###############################################################################################################################

def _add(binary_name, binary_specific):

    zato_path = os.path.join(sys.argv[1], binary_name)
    f = open(zato_path, 'w')
    f.write(template.format(executable=sys.executable, binary_specific=binary_specific, sys_path=',\n  '.join(get_sys_path())))
    f.close()

    os.chmod(zato_path, 0o755)

# ###############################################################################################################################

def add_zato():
    binary_specific = """
import zato.cli.zato_command

if __name__ == '__main__':
    sys.exit(zato.cli.zato_command.main())
"""
    _add('zato', binary_specific)

# ###############################################################################################################################

def add_py():
    binary_specific = """
_interactive = True
if len(sys.argv) > 1:
    _options, _args = __import__("getopt").getopt(sys.argv[1:], 'ic:m:')
    _interactive = False
    for (_opt, _val) in _options:
        if _opt == '-i':
            _interactive = True
        elif _opt == '-c':
            exec _val
        elif _opt == '-m':
            sys.argv[1:] = _args
            _args = []
            __import__("runpy").run_module(
                 _val, {}, "__main__", alter_sys=True)

    if _args:
        sys.argv[:] = _args
        __file__ = _args[0]
        del _options, _args
        execfile(__file__)

if _interactive:
    del _interactive
    __import__("code").interact(banner="", local=globals())

"""
    _add('py', binary_specific)
# ###############################################################################################################################


if __name__ == '__main__':
    add_zato()
    add_py()
