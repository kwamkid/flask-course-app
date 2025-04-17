"""add name field to user

Revision ID: 11f74865025f
Revises: ba9fb6cd4542
Create Date: 2025-04-17 11:00:56.040748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11f74865025f'
down_revision = 'ba9fb6cd4542'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_hash')
        batch_op.add_column(sa.Column('password', sa.String(length=200), nullable=False))
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password')
        batch_op.add_column(sa.Column('password_hash', sa.String(length=200), nullable=False))
        batch_op.drop_column('email')
        batch_op.drop_column('created_at')
