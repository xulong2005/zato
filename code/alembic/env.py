from __future__ import with_statement

# stdlib
import logging.config

# Alembic
from alembic import context

# SQLAlchemy
import sqlalchemy

# Zato
import zato.common.odb.model


# Don't mess with logging if running from within Zato.
if context.config.config_file_name is not None:
    logging.config.fileConfig(context.config.config_file_name)

target_metadata = zato.common.odb.model.Base.metadata


IGNORE_TABLES = [
    'django_site',
    'cluster_color_marker',
    'user_profile',
    'sqlite_sequence',
    'auth_user',
    'auth_group',
    'auth_permission',
    'auth_group_permissions',
    'django_content_type',
    'django_session',
    'auth_user_groups',
    'django_migrations',
    'auth_user_user_permissions',
]

def include_object(obj, name, type_, reflected, compare_to):
    return (type_ != 'table') or (name not in IGNORE_TABLES)

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(url=url, include_object=include_object)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = sqlalchemy.engine_from_config(
                context.config.get_section(context.config.config_ini_section),
                prefix='sqlalchemy.',
                poolclass=sqlalchemy.pool.NullPool)

    connection = engine.connect()
    context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=include_object,
                )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
