#!/usr/bin/env python3
"""Standalone migration script for session new word progress tracking.

Run this script directly to apply migration 003:
    python migrate_003.py [path_to_database]

Default database path: data/wordforge.db
"""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: str):
    """Apply migration 003: session new word progress table."""
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create session_new_word_progress table
        print("Creating session_new_word_progress table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_new_word_progress (
                id INTEGER PRIMARY KEY,
                session_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                exercise_1_correct BOOLEAN,
                exercise_2_correct BOOLEAN,
                exercise_3_correct BOOLEAN,
                exercise_4_correct BOOLEAN,
                learned BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES training_sessions (id),
                FOREIGN KEY (word_id) REFERENCES words (id)
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_session_new_word_progress_session_id
            ON session_new_word_progress (session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_session_new_word_progress_word_id
            ON session_new_word_progress (word_id)
        """)
        print("  - session_new_word_progress table created")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Default database path
    db_path = "data/wordforge.db"

    # Allow override via command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    # Check if file exists
    if not Path(db_path).exists():
        print(f"Error: Database not found at {db_path}")
        print("Usage: python migrate_003.py [path_to_database]")
        sys.exit(1)

    migrate(db_path)
