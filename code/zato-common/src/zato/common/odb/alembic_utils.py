# -*- coding: utf-8 -*-

"""
Functions used to support Alembic integration.

Copyright (C) 2017 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# Stdlib
import contextlib
import logging
import os
import sys

# Alembic
import alembic.config

# SQLAlchemy
import sqlalchemy

# Zato
import zato.common.odb.alembic
from zato.common.util import get_crypto_manager_from_server_config
from zato.common.util import get_engine_url
from zato.common.util import get_config as get_zato_config
from zato.common.util import get_odb_session_from_server_config


# ################################################################################################################################

def get_alembic_dir():
    """Return the location of the alembic directory in the source tree."""
    return os.path.dirname(zato.common.odb.alembic.__file__)

# ################################################################################################################################

def get_config(engine):
    """
    Instantiate Alembic with a configuration equivalent to:

    [alembic]
    script_location = <zato_basedir>/alembic
    sqlalchemy.url = <configured engine url>
    """
    config = alembic.config.Config()
    config.set_main_option('script_location', get_alembic_dir())
    config.set_main_option('sqlalchemy.url', str(engine.url))
    return config

# ################################################################################################################################

@contextlib.contextmanager
def share_connection(engine):
    """Yield an alembic Config instance that reuses ODB's existing SQLAlchemy connection. This is necessary to avoid having to duplicate the large amount of
    logic involved in setting up an mxODBC connection, etc."""
    config = get_config(engine)
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        yield config

# ################################################################################################################################

def main():
    """
    Command line wrapper that connects Alembic to the database specified in a Zato server config.
    """
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: _zato-alembic <server_path> ...\n')
        sys.exit(1)

    repo_dir = os.path.join(sys.argv[1], 'config', 'repo')
    if not os.path.isdir(repo_dir):
        sys.stderr.write('Error: {} is not a server directory.\n'.format(repo_dir))
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

    zconfig = get_zato_config(repo_dir, 'server.conf')
    cm = get_crypto_manager_from_server_config(zconfig, repo_dir)
    session = get_odb_session_from_server_config(zconfig, cm)

    command_line = alembic.config.CommandLine(prog='_zato-alembic')
    options = command_line.parser.parse_args(sys.argv[2:])
    if not hasattr(options, 'cmd'):
        command_line.parser.error("too few arguments")
        sys.exit(1)

    engine = session.connection().engine
    config = get_config(engine)
    command_line.run_cmd(config, options)
