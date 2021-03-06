"""empty message

Revision ID: 9c128cd125da
Revises: 
Create Date: 2020-05-25 18:23:27.002615

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c128cd125da'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('car_lists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=25), nullable=True),
    sa.Column('car_status', sa.String(length=10), nullable=True),
    sa.Column('company', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('company_departments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company', sa.String(length=20), nullable=True),
    sa.Column('department', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('field_permissions',
    sa.Column('field_permission_id', sa.Integer(), nullable=False),
    sa.Column('field_permission_flowmodal', sa.String(length=50), nullable=True),
    sa.Column('field_permission_node', sa.Integer(), nullable=True),
    sa.Column('field_permission_field_name', sa.String(length=25), nullable=True),
    sa.Column('field_permission_read', sa.String(length=25), nullable=True),
    sa.Column('field_permission_write', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('field_permission_id')
    )
    op.create_table('houses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=15), nullable=True),
    sa.Column('company', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('user', sa.String(length=15), nullable=True),
    sa.Column('house', sa.String(length=15), nullable=True),
    sa.Column('time', sa.Integer(), nullable=True),
    sa.Column('company', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('package_procedure_infos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('procedure_list_id', sa.Integer(), nullable=True),
    sa.Column('procedure_name', sa.String(length=15), nullable=True),
    sa.Column('logistics_company', sa.String(length=50), nullable=True),
    sa.Column('num', sa.String(length=50), nullable=True),
    sa.Column('destination_company', sa.String(length=100), nullable=True),
    sa.Column('package_name', sa.String(length=50), nullable=True),
    sa.Column('payment_method', sa.String(length=15), nullable=True),
    sa.Column('approval_person', sa.String(length=15), nullable=True),
    sa.Column('approval_department', sa.String(length=15), nullable=True),
    sa.Column('collect_person', sa.String(length=15), nullable=True),
    sa.Column('collect_department', sa.String(length=15), nullable=True),
    sa.Column('status', sa.String(length=15), nullable=True),
    sa.Column('approval_time', sa.DateTime(), nullable=True),
    sa.Column('confirm_time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('procedure_approvals',
    sa.Column('procedure_approval_id', sa.Integer(), nullable=False),
    sa.Column('procedure_approval_flowid', sa.String(length=50), nullable=True),
    sa.Column('procedure_approval_current_line_node_id', sa.Integer(), nullable=True),
    sa.Column('procedure_approval_user_id', sa.Integer(), nullable=True),
    sa.Column('procedure_approval_user_name', sa.String(length=25), nullable=True),
    sa.Column('procedure_approval_reason', sa.String(length=25), nullable=True),
    sa.Column('procedure_approval_approval_datetime', sa.DateTime(), nullable=True),
    sa.Column('procedure_approval_state', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('procedure_approval_id')
    )
    op.create_table('procedure_lines',
    sa.Column('procedure_line_id', sa.Integer(), nullable=False),
    sa.Column('procedure_line_flowmodal', sa.String(length=50), nullable=True),
    sa.Column('procedure_line_pre_line_id', sa.Integer(), nullable=True),
    sa.Column('procedure_line_pre_line_name', sa.String(length=25), nullable=True),
    sa.Column('procedure_line_next_line_id', sa.Integer(), nullable=True),
    sa.Column('procedure_line_next_line_name', sa.String(length=25), nullable=True),
    sa.Column('procedure_line_description', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('procedure_line_id')
    )
    op.create_table('procedure_lists',
    sa.Column('procedure_list_id', sa.Integer(), nullable=False),
    sa.Column('procedure_list_flowmodal', sa.String(length=50), nullable=True),
    sa.Column('procedure_list_name', sa.String(length=20), nullable=True),
    sa.Column('procedure_list_', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('procedure_list_id'),
    sa.UniqueConstraint('procedure_list_name')
    )
    op.create_table('procedure_nodes',
    sa.Column('procedure_node_id', sa.Integer(), nullable=False),
    sa.Column('procedure_node_flowmodal', sa.String(length=50), nullable=True),
    sa.Column('procedure_node_name', sa.String(length=25), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('procedure_node_role', sa.String(length=25), nullable=True),
    sa.Column('procedure_node_escription', sa.String(length=25), nullable=True),
    sa.PrimaryKeyConstraint('procedure_node_id')
    )
    op.create_table('procedure_states',
    sa.Column('procedure_state_id', sa.Integer(), nullable=False),
    sa.Column('procedure_state_flowid', sa.String(length=50), nullable=True),
    sa.Column('procedure_state', sa.Integer(), nullable=True),
    sa.Column('procedure_state_name', sa.String(length=25), nullable=True),
    sa.Column('procedure_state_flowmodal', sa.String(length=25), nullable=True),
    sa.Column('procedure_state_procedure_list_name', sa.String(length=25), nullable=True),
    sa.Column('procedure_state_user_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('procedure_state_id')
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_default'), 'roles', ['default'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('department', sa.String(length=64), nullable=True),
    sa.Column('company', sa.String(length=64), nullable=True),
    sa.Column('tel', sa.String(length=15), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
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
    sa.Column('first_approval', sa.Integer(), nullable=True),
    sa.Column('confirmer', sa.Integer(), nullable=True),
    sa.Column('miles', sa.Integer(), nullable=True),
    sa.Column('outmiles', sa.Integer(), nullable=True),
    sa.Column('company', sa.String(length=10), nullable=True),
    sa.Column('driver', sa.String(length=10), nullable=True),
    sa.Column('rejectreason', sa.String(length=100), nullable=True),
    sa.Column('procedure_no', sa.Integer(), nullable=True),
    sa.Column('current_line_node_id', sa.Integer(), nullable=True),
    sa.Column('state', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['car_id'], ['car_lists.id'], ),
    sa.ForeignKeyConstraint(['confirmer'], ['users.id'], ),
    sa.ForeignKeyConstraint(['first_approval'], ['users.id'], ),
    sa.ForeignKeyConstraint(['procedure_list_id'], ['procedure_lists.procedure_list_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('car_procedure_infos')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_default'), table_name='roles')
    op.drop_table('roles')
    op.drop_table('procedure_states')
    op.drop_table('procedure_nodes')
    op.drop_table('procedure_lists')
    op.drop_table('procedure_lines')
    op.drop_table('procedure_approvals')
    op.drop_table('package_procedure_infos')
    op.drop_table('orders')
    op.drop_table('houses')
    op.drop_table('field_permissions')
    op.drop_table('company_departments')
    op.drop_table('car_lists')
    # ### end Alembic commands ###
