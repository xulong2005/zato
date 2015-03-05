# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

en_uk = """

[main]
name              = English
top_level         = Config, Path, Handler, Pipeline

[config]
name              = Name: {name}
start             = Start: {path} from {service}
service_map       = Map service {service} to {label}

[pipeline]
pattern           = {name}: {data_type}

[path]
path              = Path: {path}

require_else      = Require {path1} else {path2}
require           = Require {path}

wait_sig_enter    = Wait for signal {signal} on timeout {timeout} enter {path}
wait_sig_invoke   = Wait for signal {signal} on timeout {timeout} invoke {service}
wait_sig          = Wait for signal {signal}

wait_sigs_enter   = Wait for signals {signals} on timeout {timeout} enter {service}
wait_sigs_invoke  = Wait for signals {signals} on timeout {timeout} invoke {service}
wait_sigs         = Wait for signals {signals}

enter             = Enter {path}
invoke            = Invoke {service}

fork_to_and_wait  = Fork to {fork_to} under {fork_name} and wait
fork_to           = Fork to {fork_to} under {fork_name}

if_invoke         = If {condition} invoke {service}
if_enter          = If {condition} enter {path}

else_invoke       = Else invoke {service}
else_enter        = Else enter {service}

emit              = Emit {event}
set               = Set {key} = {value}

[handler]
handler           = Handler: {handler}
invoke            = Invoke {service}
enter             = Enter {service}
set               = Set {key} = {value}
""".strip()
