"""Resolve disprate migration paths back into a single head

Revision ID: c2854eaa7183
Revises: ('0029b_0d1ac9c22670', '0029a_00ad4c118b99')
Create Date: 2017-12-14 15:37:29.550776

"""

# Revision identifiers, used by Alembic.
revision = '0030_c2854eaa7183'
down_revision = ('0029b_0d1ac9c22670', '0029a_00ad4c118b99')

from alembic import context, op
import sqlalchemy as sa

# Zato
from zato.common.odb import model

def upgrade():
    pass


def downgrade():
    pass
