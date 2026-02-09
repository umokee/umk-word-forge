#!/usr/bin/env python3
"""Standalone migration script for training improvements.

Run this script directly to apply migration 002:
    python migrate_002.py [path_to_database]

Default database path: data/wordforge.db
"""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: str):
    """Apply migration 002: training improvements."""
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Create daily_training_sessions table if not exists
        print("Creating daily_training_sessions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_training_sessions (
                id INTEGER PRIMARY KEY,
                category VARCHAR,
                training_date DATE,
                session_id INTEGER,
                completed_at DATETIME
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_daily_training_sessions_category
            ON daily_training_sessions (category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_daily_training_sessions_training_date
            ON daily_training_sessions (training_date)
        """)
        print("  - daily_training_sessions table created")

        # 2. Add new columns to word_contexts
        print("Adding columns to word_contexts...")

        # Get existing columns
        cursor.execute("PRAGMA table_info(word_contexts)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        columns_to_add = [
            ("context_type", "VARCHAR DEFAULT 'example'"),
            ("usage_explanation", "VARCHAR"),
            ("grammar_pattern", "VARCHAR"),
            ("common_errors", "JSON"),
        ]

        for col_name, col_def in columns_to_add:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE word_contexts ADD COLUMN {col_name} {col_def}")
                    print(f"  - Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  - Column {col_name} already exists")
                    else:
                        raise
            else:
                print(f"  - Column {col_name} already exists")

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
        print("Usage: python migrate_002.py [path_to_database]")
        sys.exit(1)

    migrate(db_path)
