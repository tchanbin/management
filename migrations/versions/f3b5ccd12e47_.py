"""empty message

Revision ID: f3b5ccd12e47
Revises: 9c128cd125da
Create Date: 2020-05-28 19:44:10.983851

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f3b5ccd12e47'
down_revision = '9c128cd125da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('field_permissions', sa.Column('field_permission_company', sa.String(length=20), nullable=True))
    op.add_column('procedure_lists', sa.Column('procedure_list_company', sa.String(length=20), nullable=True))
    op.add_column('procedure_lists', sa.Column('procedure_list_department', sa.String(length=20), nullable=True))
    op.drop_column('procedure_lists', 'procedure_list_')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('procedure_lists', sa.Column('procedure_list_', mysql.VARCHAR(length=10), nullable=True))
    op.drop_column('procedure_lists', 'procedure_list_department')
    op.drop_column('procedure_lists', 'procedure_list_company')
    op.drop_column('field_permissions', 'field_permission_company')
    # ### end Alembic commands ###
