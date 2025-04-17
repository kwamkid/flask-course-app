"""Add note to Holiday

Revision ID: ba9fb6cd4542
Revises: 
Create Date: 2025-04-15 07:43:09.696408

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba9fb6cd4542'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('classes')
    op.add_column('holiday', sa.Column('note', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('holiday', 'note')
    op.create_table('classes',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), nullable=False),
    sa.Column('course_id', sa.INTEGER(), nullable=False),
    sa.Column('total_sessions', sa.INTEGER(), nullable=False),
    sa.Column('days', sa.VARCHAR(length=50), nullable=False),
    sa.Column('start_time', sa.VARCHAR(length=5), nullable=False),
    sa.Column('end_time', sa.VARCHAR(length=5), nullable=False),
    sa.Column('start_date', sa.VARCHAR(length=10), nullable=False),
    sa.Column('schedule', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
