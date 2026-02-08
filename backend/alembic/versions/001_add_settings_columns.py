"""Add new settings columns

Revision ID: 001
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to user_settings table
    # Using batch mode for SQLite compatibility

    columns_to_add = [
        ('max_reviews_per_session', 'INTEGER', '50'),
        ('new_words_position', 'VARCHAR', "'end'"),
        ('exercise_direction', 'VARCHAR', "'mixed'"),
        ('show_transcription', 'BOOLEAN', '1'),
        ('show_example_translation', 'BOOLEAN', '1'),
        ('auto_play_audio', 'BOOLEAN', '0'),
        ('hint_delay_seconds', 'INTEGER', '10'),
        ('preferred_exercises', 'JSON', "'[]'"),
        ('keyboard_shortcuts', 'BOOLEAN', '1'),
        ('show_progress_details', 'BOOLEAN', '1'),
        ('session_end_summary', 'BOOLEAN', '1'),
        ('animation_speed', 'VARCHAR', "'normal'"),
        ('font_size', 'VARCHAR', "'normal'"),
        ('tts_enabled', 'BOOLEAN', '1'),
        ('tts_speed', 'FLOAT', '1.0'),
        ('tts_voice', 'VARCHAR', "'default'"),
        ('tts_auto_play_exercises', 'BOOLEAN', '0'),
        ('daily_goal_type', 'VARCHAR', "'words'"),
        ('daily_goal_value', 'INTEGER', '20'),
        ('gemini_api_key', 'VARCHAR', 'NULL'),
        ('ai_feedback_language', 'VARCHAR', "'ru'"),
        ('ai_difficulty_context', 'VARCHAR', "'simple'"),
    ]

    conn = op.get_bind()

    # Check which columns already exist
    result = conn.execute(sa.text("PRAGMA table_info(user_settings)"))
    existing_columns = {row[1] for row in result.fetchall()}

    for col_name, col_type, default in columns_to_add:
        if col_name not in existing_columns:
            try:
                op.execute(
                    f"ALTER TABLE user_settings ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                )
            except Exception as e:
                print(f"Column {col_name} might already exist: {e}")


def downgrade() -> None:
    # SQLite doesn't support dropping columns easily
    # Would need to recreate the table
    pass
