"""added date and time separate columns

Revision ID: 47ae5a066869
Revises: dd367c136146
Create Date: 2024-12-11 18:04:32.126699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '47ae5a066869'
down_revision = 'dd367c136146'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=False))
        batch_op.add_column(sa.Column('time', sa.Time(), nullable=False))
        batch_op.drop_column('date_time')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_time', mysql.DATETIME(), nullable=False))
        batch_op.drop_column('time')
        batch_op.drop_column('date')

    # ### end Alembic commands ###