"""Initial database schema

Revision ID: b16dbad4c2be
Revises: 
Create Date: 2025-07-08 16:11:44.997699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b16dbad4c2be'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('companies',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('domain', sa.String(length=255), nullable=True),
    sa.Column('logo_url', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_domain'), 'companies', ['domain'], unique=True)
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)
    op.create_table('system_config',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_config_id'), 'system_config', ['id'], unique=False)
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=True)
    op.create_table('sites',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('site_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('contact_email', sa.String(length=255), nullable=True),
    sa.Column('contact_phone', sa.String(length=50), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sites_id'), 'sites', ['id'], unique=False)
    op.create_index(op.f('ix_sites_site_id'), 'sites', ['site_id'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=50), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_ldap_user', sa.Boolean(), nullable=True),
    sa.Column('ldap_dn', sa.String(length=500), nullable=True),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('agents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('pc_name', sa.String(length=255), nullable=False),
    sa.Column('pc_ip', sa.String(length=45), nullable=True),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('agent_version', sa.String(length=50), nullable=True),
    sa.Column('os_version', sa.String(length=255), nullable=True),
    sa.Column('api_key', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('last_job_submitted', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_jobs_submitted', sa.Integer(), nullable=True),
    sa.Column('pending_jobs', sa.Integer(), nullable=True),
    sa.Column('config_version', sa.Integer(), nullable=True),
    sa.Column('installed_printers', sa.Text(), nullable=True),
    sa.Column('site_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('api_key')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_index(op.f('ix_agents_pc_name'), 'agents', ['pc_name'], unique=False)
    op.create_index(op.f('ix_agents_username'), 'agents', ['username'], unique=False)
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_table('printers',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('model', sa.String(length=255), nullable=True),
    sa.Column('is_color', sa.Boolean(), nullable=True),
    sa.Column('is_duplex_capable', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('site_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_printers_id'), 'printers', ['id'], unique=False)
    op.create_index(op.f('ix_printers_ip_address'), 'printers', ['ip_address'], unique=False)
    op.create_index(op.f('ix_printers_name'), 'printers', ['name'], unique=False)
    op.create_table('print_jobs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('pc_name', sa.String(length=255), nullable=False),
    sa.Column('printer_name', sa.String(length=255), nullable=False),
    sa.Column('printer_ip', sa.String(length=45), nullable=True),
    sa.Column('document_name', sa.String(length=500), nullable=False),
    sa.Column('pages', sa.Integer(), nullable=False),
    sa.Column('copies', sa.Integer(), nullable=True),
    sa.Column('total_pages', sa.Integer(), nullable=False),
    sa.Column('is_duplex', sa.Boolean(), nullable=True),
    sa.Column('is_color', sa.Boolean(), nullable=True),
    sa.Column('print_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('agent_version', sa.String(length=50), nullable=True),
    sa.Column('job_size_bytes', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('agent_id', sa.Integer(), nullable=True),
    sa.Column('printer_id', sa.Integer(), nullable=True),
    sa.Column('site_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ),
    sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_print_jobs_id'), 'print_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_print_jobs_pc_name'), 'print_jobs', ['pc_name'], unique=False)
    op.create_index(op.f('ix_print_jobs_print_time'), 'print_jobs', ['print_time'], unique=False)
    op.create_index(op.f('ix_print_jobs_printer_name'), 'print_jobs', ['printer_name'], unique=False)
    op.create_index(op.f('ix_print_jobs_username'), 'print_jobs', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_print_jobs_username'), table_name='print_jobs')
    op.drop_index(op.f('ix_print_jobs_printer_name'), table_name='print_jobs')
    op.drop_index(op.f('ix_print_jobs_print_time'), table_name='print_jobs')
    op.drop_index(op.f('ix_print_jobs_pc_name'), table_name='print_jobs')
    op.drop_index(op.f('ix_print_jobs_id'), table_name='print_jobs')
    op.drop_table('print_jobs')
    op.drop_index(op.f('ix_printers_name'), table_name='printers')
    op.drop_index(op.f('ix_printers_ip_address'), table_name='printers')
    op.drop_index(op.f('ix_printers_id'), table_name='printers')
    op.drop_table('printers')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_agents_username'), table_name='agents')
    op.drop_index(op.f('ix_agents_pc_name'), table_name='agents')
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.drop_table('agents')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_sites_site_id'), table_name='sites')
    op.drop_index(op.f('ix_sites_id'), table_name='sites')
    op.drop_table('sites')
    op.drop_index(op.f('ix_system_config_key'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_id'), table_name='system_config')
    op.drop_table('system_config')
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_index(op.f('ix_companies_id'), table_name='companies')
    op.drop_index(op.f('ix_companies_domain'), table_name='companies')
    op.drop_table('companies')
    # ### end Alembic commands ###
