"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-20 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- ENUMS ---
    op.execute("CREATE TYPE userrole AS ENUM ('reader','maintainer','admin')")
    op.execute("CREATE TYPE usecasestatus AS ENUM ('new','under_review','approved','in_progress','completed','archived')")
    op.execute("CREATE TYPE relationtype AS ENUM ('depends_on','complements','conflicts_with','duplicates')")
    op.execute("CREATE TYPE transcriptstatus AS ENUM ('uploaded','processing','completed','failed')")

    # --- industries ---
    op.create_table(
        'industries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(320), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(1024), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('role', postgresql.ENUM('reader','maintainer','admin',
                  name='userrole', create_type=False),
                  nullable=False, server_default='reader'),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- companies ---
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('website', sa.String(512), nullable=True),
        sa.Column('industry_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('industries.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_companies_industry_id', 'companies', ['industry_id'])

    # --- transcripts ---
    op.create_table(
        'transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('raw_text', sa.Text, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', postgresql.ENUM('uploaded','processing','completed','failed',
                  name='transcriptstatus', create_type=False),
                  nullable=False, server_default='uploaded'),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.Column('chunk_count', sa.Integer, nullable=True),
        sa.Column('chunks_processed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_transcripts_company_id', 'transcripts', ['company_id'])
    op.create_index('ix_transcripts_status', 'transcripts', ['status'])

    # --- use_cases ---
    op.create_table(
        'use_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('expected_benefit', sa.Text, nullable=True),
        sa.Column('status', postgresql.ENUM('new','under_review','approved',
                  'in_progress','completed','archived',
                  name='usecasestatus', create_type=False),
                  nullable=False, server_default='new'),
        sa.Column('confidence_score', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('effort_score', sa.Integer, nullable=True),
        sa.Column('impact_score', sa.Integer, nullable=True),
        sa.Column('complexity_score', sa.Integer, nullable=True),
        sa.Column('strategic_score', sa.Integer, nullable=True),
        sa.Column('priority_score', sa.Float, nullable=True),
        sa.Column('tags', postgresql.JSON, nullable=True, server_default='[]'),
        sa.Column('qdrant_id', sa.String(255), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('transcripts.id'), nullable=True),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_use_cases_company_id', 'use_cases', ['company_id'])
    op.create_index('ix_use_cases_status', 'use_cases', ['status'])
    op.create_index('ix_use_cases_assignee_id', 'use_cases', ['assignee_id'])
    op.create_index('ix_use_cases_confidence', 'use_cases', ['confidence_score'])
    op.create_index('ix_use_cases_transcript_id', 'use_cases', ['transcript_id'])

    # --- use_case_relations ---
    op.create_table(
        'use_case_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('use_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('use_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', postgresql.ENUM('depends_on','complements',
                  'conflicts_with','duplicates', name='relationtype', create_type=False),
                  nullable=False),
        sa.Column('note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_uc_relations_source', 'use_case_relations', ['source_id'])
    op.create_index('ix_uc_relations_target', 'use_case_relations', ['target_id'])

    # --- comments ---
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('use_case_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('use_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_comments_use_case_id', 'comments', ['use_case_id'])


def downgrade() -> None:
    op.drop_table('comments')
    op.drop_table('use_case_relations')
    op.drop_table('use_cases')
    op.drop_table('transcripts')
    op.drop_table('companies')
    op.drop_table('users')
    op.drop_table('industries')
    op.execute("DROP TYPE userrole")
    op.execute("DROP TYPE usecasestatus")
    op.execute("DROP TYPE relationtype")
    op.execute("DROP TYPE transcriptstatus")
