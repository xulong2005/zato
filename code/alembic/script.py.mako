"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}

"""

# Revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}

from alembic import context, op
import sqlalchemy as sa
${imports if imports else ""}

# Zato
from zato.common.odb import model

# Pass this as a naming_convention= kwarg to batch_alter_table() in order to
# resolve unnamed constraint exceptions with SQLite. This is the default
# format used by PostgreSQL, it is likely if there are other databases to
# be supported, we will need to mimic their default naming behaviour by
# dynamically switching this at runtime, according to the driver in use.
naming_convention = {
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
