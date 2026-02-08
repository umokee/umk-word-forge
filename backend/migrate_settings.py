#!/usr/bin/env python3
"""Standalone migration script to add missing columns to user_settings table."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.database import engine
from sqlalchemy import text


def migrate():
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

    with engine.connect() as conn:
        # Get existing columns
        result = conn.execute(text("PRAGMA table_info(user_settings)"))
        existing_columns = {row[1] for row in result.fetchall()}
        print(f"Existing columns: {existing_columns}")

        added = 0
        for col_name, col_type, default in columns_to_add:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE user_settings ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                    conn.execute(text(sql))
                    print(f"  Added column: {col_name}")
                    added += 1
                except Exception as e:
                    print(f"  Error adding {col_name}: {e}")
            else:
                print(f"  Column {col_name} already exists")

        conn.commit()
        print(f"\nMigration complete. Added {added} new columns.")


if __name__ == "__main__":
    migrate()
