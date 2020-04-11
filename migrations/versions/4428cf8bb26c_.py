"""empty message

Revision ID: 4428cf8bb26c
Revises: c91b579c730a
Create Date: 2020-04-08 20:08:44.730880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4428cf8bb26c'
down_revision = 'c91b579c730a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('car_lists', sa.Column('company', sa.String(length=10), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('car_lists', 'company')
    # ### end Alembic commands ###
