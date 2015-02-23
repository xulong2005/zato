# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Actors
# Acivities
# Decisions (w/ defaults)
# Conditions
# Checkpoints
# Fork/Join
# Cancel
# Signal (world -> process)
# Notifications (process -> world)
# Sub-processes
# Start points labeled to make the intent of the process explicit
# End points

"""
Context:

  Start: 'first.create' from 'my.channel.create.user'

  Map service 'adapter.crm.create.user' to 'create.crm'
  Map service 'adapter.billing.create.user' to 'create.billing'
  Map service 'adapter.oss.create.user' to 'create.oss'

  Map service 'adapter.crm.delete.user' to 'delete.crm'
  Map service 'adapter.billing.delete.user' to 'delete.billing'

  Pipeline:
    user_name: str
    user_id: int
    user_addresses: list
    user_social: dict

Path: first.create

  Fork to 'create.crm, create.billing' under 'create.crm.billing.fork' and wait
  If 'create.crm.billing.fork.all_ok' call 'second.create'
  Else call 'rollback.first.create'

Path: second.create

  Invoke 'create.oss'
  Emit 'user.created'

Path: rollback.first.create

  Fork to 'delete.crm, delete.billing'
  Emit 'user.created'
"""

"""
Context:

  Start: 'order.management' from 'my.channel.feasibility-study'

Path: order.management

  Steps:

    Require 'feasibility.study' or 'reject.order'
    Wait for signals 'patch.complete, drop.complete'
    Call 'order.complete'

Handler: cease
  Ignore signals: amend, *.complete

  Invoke core.order.release-resources
  Invoke core.order.on-cease

Handler: amend
  Invoke core.order.amend

Handler: patch.complete
  Invoke core.order.patch-complete

Handler: drop.complete
  Invoke core.order.on-drop-complete

Path: feasibility.study
  Invoke 'core.order.feasibility-study'

Path: order.complete
  Invoke 'core.order.notify-complete'
  
Path: reject.order
  Invoke 'core.order.reject'
  Emit 'order.rejected'
"""