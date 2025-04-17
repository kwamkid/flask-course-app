"""update user model fields

Revision ID: 55374012e5bf
Revises: 11f74865025f
Create Date: 2025-04-17 11:03:31.318026

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55374012e5bf'
down_revision = '11f74865025f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=False))
        batch_op.create_unique_constraint('uq_user_email', ['email'])

def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.drop_column('email')
