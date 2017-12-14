"""
Functions used to support Alembic integration.
"""

import contextlib
import os

import alembic.config


def get_alembic_dir():
    """Return the location of the alembic directory in the source tree."""
    path = __file__
    for _ in xrange(6):
        path, _ = os.path.split(path)
    return os.path.join(path, 'alembic')


def get_config(engine):
    """
    Instantiate Alembic with a configuration equivalent to:

    [alembic]
    script_location = <zato_basedir>/alembic
    sqlalchemy.url = <configured engine url>
    """
    config = alembic.config.Config()
    config.set_main_option('script_location', get_alembic_dir())
    config.set_main_option('sqlalchemy.url', engine.url)
    return config


@contextlib.contextmanager
def share_connection(engine):
    """
    Yield an alembic Config instance that reuses ODB's existing SQLAlchemy
    connection. This is necessary to avoid having to duplicate the large amount
    of logic involved in setting up an mxODBC connection, etc.
    """
    config = get_config()
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        yield config
