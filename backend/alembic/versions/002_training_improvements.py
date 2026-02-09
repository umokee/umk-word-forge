"""Training system improvements: daily limits and rich contexts

Revision ID: 002
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa


revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create daily_training_sessions table
    op.create_table(
        'daily_training_sessions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('category', sa.String, index=True),  # "words", "phrasal", "irregular"
        sa.Column('training_date', sa.Date, index=True),
        sa.Column('session_id', sa.Integer, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # 2. Add new columns to word_contexts table for rich contexts
    conn = op.get_bind()

    # Check which columns already exist in word_contexts
    result = conn.execute(sa.text("PRAGMA table_info(word_contexts)"))
    existing_columns = {row[1] for row in result.fetchall()}

    columns_to_add = [
        ('context_type', 'VARCHAR', "'example'"),  # "example", "usage_rule", "comparison"
        ('usage_explanation', 'VARCHAR', 'NULL'),  # "Use 'the' for specific items"
        ('grammar_pattern', 'VARCHAR', 'NULL'),    # "the + noun"
        ('common_errors', 'JSON', 'NULL'),         # [{"wrong": "...", "correct": "...", "why": "..."}]
    ]

    for col_name, col_type, default in columns_to_add:
        if col_name not in existing_columns:
            try:
                op.execute(
                    f"ALTER TABLE word_contexts ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                )
            except Exception as e:
                print(f"Column {col_name} might already exist: {e}")


def downgrade() -> None:
    # Drop daily_training_sessions table
    op.drop_table('daily_training_sessions')

    # SQLite doesn't support dropping columns easily
    # Would need to recreate the table for word_contexts columns
    pass
