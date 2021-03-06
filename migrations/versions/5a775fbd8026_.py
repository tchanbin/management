"""empty message

Revision ID: 5a775fbd8026
Revises: c330e431fb40
Create Date: 2020-07-18 15:43:18.968372

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5a775fbd8026'
down_revision = 'c330e431fb40'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('procedure_states', 'procedure_state_approval_time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procedure_states', sa.Column('procedure_state_approval_time', mysql.DATETIME(), nullable=True))
    # ### end Alembic commands ###
