"""empty message

Revision ID: 8b97d15a427e
Revises: 398c6ff662ac
Create Date: 2020-05-28 21:10:13.361900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b97d15a427e'
down_revision = '398c6ff662ac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('car_procedure_infos',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('procedure_list_id', sa.Integer(), nullable=True),
    sa.Column('procedure_list_flowmodal', sa.String(length=50), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('tel', sa.String(length=15), nullable=True),
    sa.Column('department', sa.String(length=64), nullable=True),
    sa.Column('car_id', sa.Integer(), nullable=True),
    sa.Column('approval_time', sa.DateTime(), nullable=True),
    sa.Column('book_start_datetime', sa.DATETIME(), nullable=True),
    sa.Column('book_end_datetime', sa.DATETIME(), nullable=True),
    sa.Column('actual_start_datetime', sa.DATETIME(), nullable=True),
    sa.Column('actual_end_datetime', sa.DATETIME(), nullable=True),
    sa.Column('number', sa.String(length=20), nullable=True),
    sa.Column('namelist', sa.String(length=50), nullable=True),
    sa.Column('reason', sa.String(length=128), nullable=True),
    sa.Column('etc', sa.Boolean(), nullable=True),
    sa.Column('arrival_place', sa.String(length=30), nullable=True),
    sa.Column('miles', sa.Integer(), nullable=True),
    sa.Column('outmiles', sa.Integer(), nullable=True),
    sa.Column('company', sa.String(length=10), nullable=True),
    sa.Column('driver', sa.String(length=10), nullable=True),
    sa.Column('rejectreason', sa.String(length=100), nullable=True),
    sa.Column('procedure_no', sa.Integer(), nullable=True),
    sa.Column('current_line_node_id', sa.Integer(), nullable=True),
    sa.Column('state', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['car_id'], ['car_lists.id'], ),
    sa.ForeignKeyConstraint(['procedure_list_id'], ['procedure_lists.procedure_list_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('car_procedure_infos')
    # ### end Alembic commands ###