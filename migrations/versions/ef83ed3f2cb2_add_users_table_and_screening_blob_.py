"""add users table and screening blob columns

Revision ID: ef83ed3f2cb2
Revises: 523230eb359a
Create Date: 2026-09-03 21:09:13.370165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef83ed3f2cb2'
down_revision: Union[str, Sequence[str], None] = '523230eb359a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table for Google OAuth authentication.
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('avatar_url', sa.String(length=1024), nullable=True),
        sa.Column('google_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    # Add user_id and resume_blob_url columns to screening_results.
    op.add_column('screening_results', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.add_column('screening_results', sa.Column('resume_blob_url', sa.String(length=1024), nullable=True))
    op.create_index('ix_screening_results_user_id', 'screening_results', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_screening_results_user_id', table_name='screening_results')
    op.drop_column('screening_results', 'resume_blob_url')
    op.drop_column('screening_results', 'user_id')
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
