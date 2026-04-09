"""add source_ip to cognitive_profiles

Revision ID: add_source_ip_cognitive
Revises: bd73bd710c30
Create Date: 2026-04-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_source_ip_cognitive'
down_revision = 'bd73bd710c30'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add source_ip column to cognitive_profiles table
    # Check if column exists first (for SQLite compatibility)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('cognitive_profiles')]
    
    if 'source_ip' not in columns:
        op.add_column('cognitive_profiles', 
            sa.Column('source_ip', sa.String(45), nullable=True)
        )
        # Create index on source_ip
        try:
            op.create_index('ix_cognitive_profiles_source_ip', 'cognitive_profiles', ['source_ip'])
        except Exception:
            pass  # Index might already exist


def downgrade() -> None:
    # Drop index first
    try:
        op.drop_index('ix_cognitive_profiles_source_ip', table_name='cognitive_profiles')
    except Exception:
        pass
    # Drop column
    op.drop_column('cognitive_profiles', 'source_ip')