"""add embedding column

Revision ID: acbf72d23f2e
Revises: 7dee80e39bb1
Create Date: 2026-01-14 03:47:47.900278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'acbf72d23f2e'
down_revision: Union[str, Sequence[str], None] = '7dee80e39bb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
     # pgvector拡張を有効化
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    op.add_column('minutes', sa.Column('embedding', Vector(768), nullable=True))
    
    # 検索用インデックスを作成（IVFFlat）
    op.execute('''
        CREATE INDEX IF NOT EXISTS idx_minutes_embedding
        ON minutes
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')

def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP INDEX IF EXISTS idx_minutes_embedding')
    op.drop_column('minutes', 'embedding')
