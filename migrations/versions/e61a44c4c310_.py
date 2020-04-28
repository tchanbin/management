"""empty message

Revision ID: e61a44c4c310
Revises: 3162ff3bb62f
Create Date: 2020-04-16 19:49:37.836913

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e61a44c4c310'
down_revision = '3162ff3bb62f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('company', sa.String(length=10), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'company')
    # ### end Alembic commands ###