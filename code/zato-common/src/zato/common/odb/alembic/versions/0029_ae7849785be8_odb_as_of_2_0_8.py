"""ODB as of 2.0.8

Revision ID: ae7849785be8
Revises: 0028_ae3419a9
Create Date: 2017-12-14 15:13:37.957627

"""

# Revision identifiers, used by Alembic.
revision = '0029_ae7849785be8'
down_revision = '0028_ae3419a9'

from alembic import context, op
import sqlalchemy as sa

# Zato
from zato.common.odb import model

def upgrade():
    pass


def downgrade():
    pass
