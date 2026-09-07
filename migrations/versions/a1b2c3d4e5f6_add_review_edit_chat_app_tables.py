"""add resume review, edit, chat, and application tables

Revision ID: a1b2c3d4e5f6
Revises: 7c2a91d4f6b9
Create Date: 2026-09-07 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7c2a91d4f6b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'resume_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('resume_filename', sa.String(length=255), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=False),
        sa.Column('review_type', sa.String(length=20), nullable=False),
        sa.Column('review_result', sa.JSON(), nullable=False),
        sa.Column('jd_text', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('llm_model_used', sa.String(length=100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resume_reviews_user_id', 'resume_reviews', ['user_id'], unique=False)

    op.create_table(
        'resume_edit_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('resume_filename', sa.String(length=255), nullable=True),
        sa.Column('resume_blob_url', sa.String(length=1024), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('undo_stack', sa.JSON(), nullable=False),
        sa.Column('redo_stack', sa.JSON(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resume_edit_sessions_user_id', 'resume_edit_sessions', ['user_id'], unique=False)

    op.create_table(
        'resume_chat_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('edit_session_id', sa.String(length=36), nullable=True),
        sa.Column('screening_id', sa.String(length=36), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=False),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('jd_text', sa.Text(), nullable=True),
        sa.Column('history', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resume_chat_sessions_user_id', 'resume_chat_sessions', ['user_id'], unique=False)

    op.create_table(
        'job_applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('edit_session_id', sa.String(length=36), nullable=True),
        sa.Column('screening_id', sa.String(length=36), nullable=True),
        sa.Column('job_id', sa.String(length=36), nullable=True),
        sa.Column('final_resume_text', sa.Text(), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_applications_user_id', 'job_applications', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_job_applications_user_id', table_name='job_applications')
    op.drop_table('job_applications')
    op.drop_index('ix_resume_chat_sessions_user_id', table_name='resume_chat_sessions')
    op.drop_table('resume_chat_sessions')
    op.drop_index('ix_resume_edit_sessions_user_id', table_name='resume_edit_sessions')
    op.drop_table('resume_edit_sessions')
    op.drop_index('ix_resume_reviews_user_id', table_name='resume_reviews')
    op.drop_table('resume_reviews')
