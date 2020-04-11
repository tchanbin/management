"""empty message

Revision ID: 6c2c69c5d692
Revises: 4428cf8bb26c
Create Date: 2020-04-08 20:38:33.144143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c2c69c5d692'
down_revision = '4428cf8bb26c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('car_procedure_infos', sa.Column('company', sa.String(length=10), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('car_procedure_infos', 'company')
    # ### end Alembic commands ###
