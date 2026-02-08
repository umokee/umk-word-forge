#!/usr/bin/env python3
"""Simple standalone migration script for SQLite database."""

import sqlite3
import os

# Try common database locations
DB_PATHS = [
    "/var/lib/wordforge/data/wordforge.db",  # Production
    "data/wordforge.db",  # Local dev
    "./wordforge.db",  # Current dir
]

def find_db():
    # Check DATABASE_URL env var first
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        path = db_url.replace("sqlite:///", "")
        if os.path.exists(path):
            return path

    for path in DB_PATHS:
        if os.path.exists(path):
            return path
    return None

def migrate():
    db_path = find_db()
    if not db_path:
        print("Database not found. Checked paths:")
        for p in DB_PATHS:
            print(f"  - {p}")
        return

    print(f"Found database: {db_path}")

    columns_to_add = [
        ('max_reviews_per_session', 'INTEGER', '50'),
        ('new_words_position', 'TEXT', "'end'"),
        ('exercise_direction', 'TEXT', "'mixed'"),
        ('show_transcription', 'INTEGER', '1'),
        ('show_example_translation', 'INTEGER', '1'),
        ('auto_play_audio', 'INTEGER', '0'),
        ('hint_delay_seconds', 'INTEGER', '10'),
        ('preferred_exercises', 'TEXT', "'[]'"),
        ('keyboard_shortcuts', 'INTEGER', '1'),
        ('show_progress_details', 'INTEGER', '1'),
        ('session_end_summary', 'INTEGER', '1'),
        ('animation_speed', 'TEXT', "'normal'"),
        ('font_size', 'TEXT', "'normal'"),
        ('tts_enabled', 'INTEGER', '1'),
        ('tts_speed', 'REAL', '1.0'),
        ('tts_voice', 'TEXT', "'default'"),
        ('tts_auto_play_exercises', 'INTEGER', '0'),
        ('daily_goal_type', 'TEXT', "'words'"),
        ('daily_goal_value', 'INTEGER', '20'),
        ('gemini_api_key', 'TEXT', 'NULL'),
        ('ai_feedback_language', 'TEXT', "'ru'"),
        ('ai_difficulty_context', 'TEXT', "'simple'"),
    ]

    # Words table - linguistic enrichment
    words_columns = [
        ('verb_forms', 'TEXT', 'NULL'),
        ('collocations', 'TEXT', 'NULL'),
        ('phrasal_verbs', 'TEXT', 'NULL'),
        ('usage_notes', 'TEXT', 'NULL'),
        ('ai_enriched', 'INTEGER', '0'),
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(user_settings)")
    existing = {row[1] for row in cursor.fetchall()}
    print(f"Existing columns ({len(existing)}): {sorted(existing)}")

    added = 0
    for col_name, col_type, default in columns_to_add:
        if col_name not in existing:
            try:
                sql = f"ALTER TABLE user_settings ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                cursor.execute(sql)
                print(f"  + Added: {col_name}")
                added += 1
            except Exception as e:
                print(f"  ! Error adding {col_name}: {e}")
        else:
            print(f"  - Exists: {col_name}")

    conn.commit()
    print(f"Settings table: added {added} new columns.")

    # Migrate words table
    cursor.execute("PRAGMA table_info(words)")
    existing_words = {row[1] for row in cursor.fetchall()}
    print(f"Words table columns: {sorted(existing_words)}")

    added_words = 0
    for col_name, col_type, default in words_columns:
        if col_name not in existing_words:
            try:
                sql = f"ALTER TABLE words ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                cursor.execute(sql)
                print(f"  + Added to words: {col_name}")
                added_words += 1
            except Exception as e:
                print(f"  ! Error adding {col_name} to words: {e}")

    conn.commit()
    conn.close()
    print(f"Words table: added {added_words} new columns.")
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
