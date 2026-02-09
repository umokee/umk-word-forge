#!/usr/bin/env python3
"""Standalone migration script to mark function words and add usage rules.

Run this script directly to apply migration 004:
    python migrate_004_function_words.py [path_to_database]

Default database path: data/wordforge.db
"""

import sqlite3
import json
import sys
from pathlib import Path


# Common function words that need special treatment
FUNCTION_WORDS = {
    # Articles
    "the": {
        "category": "function",
        "part_of_speech": "article",
        "usage_rules": [
            {"rule": "Используется с определенными/конкретными предметами", "example": "The book on the table is mine."},
            {"rule": "Перед уникальными объектами", "example": "The sun, the moon, the Earth"},
            {"rule": "Перед превосходной степенью", "example": "She is the best student."},
            {"rule": "С названиями океанов, рек, пустынь", "example": "The Pacific Ocean, the Nile, the Sahara"},
        ],
        "comparisons": [
            {"vs": "a/an", "difference": "the - конкретный предмет, a/an - любой из группы"},
        ],
        "common_errors": [
            {"wrong": "I go to the school.", "correct": "I go to school.", "why": "school как институт, не здание"},
            {"wrong": "The life is beautiful.", "correct": "Life is beautiful.", "why": "жизнь в общем, не конкретная"},
        ]
    },
    "a": {
        "category": "function",
        "part_of_speech": "article",
        "usage_rules": [
            {"rule": "Перед исчисляемыми существительными в ед. числе", "example": "I have a car."},
            {"rule": "При первом упоминании", "example": "I saw a dog. The dog was big."},
            {"rule": "В значении 'один'", "example": "Wait a minute."},
            {"rule": "С профессиями", "example": "She is a doctor."},
        ],
        "comparisons": [
            {"vs": "an", "difference": "a перед согласным звуком, an перед гласным"},
            {"vs": "the", "difference": "a/an - неопределенный, the - определенный"},
        ],
        "common_errors": [
            {"wrong": "He is doctor.", "correct": "He is a doctor.", "why": "профессии требуют артикль"},
        ]
    },
    "an": {
        "category": "function",
        "part_of_speech": "article",
        "usage_rules": [
            {"rule": "Перед словами, начинающимися с гласного звука", "example": "an apple, an hour"},
            {"rule": "Важен звук, а не буква", "example": "a university (звук /j/), an honest (h немое)"},
        ],
        "common_errors": [
            {"wrong": "a umbrella", "correct": "an umbrella", "why": "начинается с гласного звука"},
            {"wrong": "an university", "correct": "a university", "why": "звук /j/ - согласный"},
        ]
    },
    # Prepositions
    "to": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Направление движения", "example": "I'm going to the store."},
            {"rule": "Перед инфинитивом", "example": "I want to learn English."},
            {"rule": "Получатель действия", "example": "Give this book to her."},
            {"rule": "Время (до)", "example": "From 9 to 5."},
        ],
        "common_errors": [
            {"wrong": "I go to home.", "correct": "I go home.", "why": "home без предлога в значении направления"},
            {"wrong": "I want to can help.", "correct": "I want to help.", "why": "после to не может быть модального глагола"},
        ]
    },
    "in": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Внутри закрытого пространства", "example": "in the room, in the box"},
            {"rule": "Месяцы, годы, века", "example": "in January, in 2024, in the 21st century"},
            {"rule": "Время суток (кроме night)", "example": "in the morning, in the evening"},
            {"rule": "Страны, города", "example": "in Russia, in Moscow"},
        ],
        "comparisons": [
            {"vs": "at", "difference": "in - внутри пространства, at - точка на карте"},
            {"vs": "on", "difference": "in - внутри, on - на поверхности"},
        ]
    },
    "on": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "На поверхности", "example": "on the table, on the wall"},
            {"rule": "Дни недели, даты", "example": "on Monday, on July 4th"},
            {"rule": "Улицы (с названием)", "example": "on Baker Street"},
            {"rule": "Транспорт (большой)", "example": "on the bus, on the plane"},
        ],
        "comparisons": [
            {"vs": "in", "difference": "on - поверхность, in - внутри"},
            {"vs": "at", "difference": "on - день/дата, at - точное время"},
        ]
    },
    "at": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Точное время", "example": "at 5 o'clock, at noon, at midnight"},
            {"rule": "Точка, место", "example": "at the bus stop, at the door"},
            {"rule": "События, мероприятия", "example": "at the party, at the concert"},
            {"rule": "Устойчивые выражения", "example": "at home, at work, at school"},
        ],
        "common_errors": [
            {"wrong": "at the morning", "correct": "in the morning", "why": "части суток используют in"},
            {"wrong": "at Monday", "correct": "on Monday", "why": "дни недели используют on"},
        ]
    },
    "for": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Длительность времени", "example": "for two hours, for a week"},
            {"rule": "Цель, назначение", "example": "This is for you."},
            {"rule": "В пользу чего-то", "example": "I voted for this idea."},
        ],
        "comparisons": [
            {"vs": "since", "difference": "for - период (for 2 years), since - точка начала (since 2020)"},
            {"vs": "during", "difference": "for - как долго, during - когда именно"},
        ]
    },
    "with": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Совместное действие", "example": "I went with my friend."},
            {"rule": "Инструмент", "example": "Cut it with a knife."},
            {"rule": "Характеристика", "example": "A man with a beard."},
        ]
    },
    "by": {
        "category": "preposition",
        "part_of_speech": "preposition",
        "usage_rules": [
            {"rule": "Автор, исполнитель", "example": "A book by Tolstoy."},
            {"rule": "Способ/средство", "example": "by car, by email, by hand"},
            {"rule": "Рядом", "example": "Sit by me."},
            {"rule": "Крайний срок", "example": "Finish by Monday."},
        ]
    },
    # Pronouns
    "it": {
        "category": "function",
        "part_of_speech": "pronoun",
        "usage_rules": [
            {"rule": "Заменяет неодушевленные существительные", "example": "The book is good. It is interesting."},
            {"rule": "Безличные предложения", "example": "It is raining. It is cold."},
            {"rule": "Формальное подлежащее", "example": "It is important to study."},
            {"rule": "Время, дата, расстояние", "example": "It is 5 o'clock. It is Monday."},
        ]
    },
    "this": {
        "category": "function",
        "part_of_speech": "pronoun",
        "usage_rules": [
            {"rule": "Указывает на близкий предмет", "example": "This book is mine. (рядом)"},
            {"rule": "Текущий момент времени", "example": "this week, this year"},
        ],
        "comparisons": [
            {"vs": "that", "difference": "this - близко, that - далеко"},
        ]
    },
    "that": {
        "category": "function",
        "part_of_speech": "pronoun",
        "usage_rules": [
            {"rule": "Указывает на далекий предмет", "example": "That car over there is expensive."},
            {"rule": "Союз в придаточных", "example": "I think that you are right."},
        ],
        "comparisons": [
            {"vs": "this", "difference": "that - далеко, this - близко"},
            {"vs": "which", "difference": "that - ограничительное, which - неограничительное"},
        ]
    },
}


def migrate(db_path: str):
    """Apply migration 004: function words and usage rules."""
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if word_category column exists
        cursor.execute("PRAGMA table_info(words)")
        columns = [col[1] for col in cursor.fetchall()]

        if "word_category" not in columns:
            print("Adding word_category column to words table...")
            cursor.execute("ALTER TABLE words ADD COLUMN word_category TEXT DEFAULT 'regular'")

        if "grammar_notes" not in columns:
            print("Adding grammar_notes column to words table...")
            cursor.execute("ALTER TABLE words ADD COLUMN grammar_notes TEXT")

        # Check if context_type column exists in word_contexts
        cursor.execute("PRAGMA table_info(word_contexts)")
        context_columns = [col[1] for col in cursor.fetchall()]

        if "context_type" not in context_columns:
            print("Adding context_type column to word_contexts table...")
            cursor.execute("ALTER TABLE word_contexts ADD COLUMN context_type TEXT DEFAULT 'example'")

        if "usage_explanation" not in context_columns:
            print("Adding usage_explanation column to word_contexts table...")
            cursor.execute("ALTER TABLE word_contexts ADD COLUMN usage_explanation TEXT")

        if "common_errors" not in context_columns:
            print("Adding common_errors column to word_contexts table...")
            cursor.execute("ALTER TABLE word_contexts ADD COLUMN common_errors TEXT")

        conn.commit()
        print("Schema updated.")

        # Update function words
        updated = 0
        added_rules = 0

        for english, data in FUNCTION_WORDS.items():
            # Find the word
            cursor.execute("SELECT id FROM words WHERE english = ?", (english,))
            row = cursor.fetchone()

            if row:
                word_id = row[0]

                # Update word category
                cursor.execute(
                    "UPDATE words SET word_category = ?, part_of_speech = ? WHERE id = ?",
                    (data["category"], data["part_of_speech"], word_id)
                )

                # Store comparisons in grammar_notes
                if "comparisons" in data:
                    cursor.execute(
                        "UPDATE words SET grammar_notes = ? WHERE id = ?",
                        (json.dumps({"comparisons": data["comparisons"]}), word_id)
                    )

                updated += 1
                print(f"  Updated: {english}")

                # Add usage rules as contexts
                if "usage_rules" in data:
                    for rule in data["usage_rules"]:
                        # Check if this rule already exists
                        cursor.execute(
                            """SELECT id FROM word_contexts
                            WHERE word_id = ? AND context_type = 'usage_rule' AND usage_explanation = ?""",
                            (word_id, rule["rule"])
                        )
                        if not cursor.fetchone():
                            cursor.execute(
                                """INSERT INTO word_contexts
                                (word_id, sentence_en, sentence_ru, source, context_type, usage_explanation)
                                VALUES (?, ?, '', 'seed', 'usage_rule', ?)""",
                                (word_id, rule.get("example", ""), rule["rule"])
                            )
                            added_rules += 1

                # Add common errors as contexts
                if "common_errors" in data:
                    for error in data["common_errors"]:
                        cursor.execute(
                            """SELECT id FROM word_contexts
                            WHERE word_id = ? AND context_type = 'comparison' AND sentence_en = ?""",
                            (word_id, error["correct"])
                        )
                        if not cursor.fetchone():
                            cursor.execute(
                                """INSERT INTO word_contexts
                                (word_id, sentence_en, sentence_ru, source, context_type, common_errors)
                                VALUES (?, ?, '', 'seed', 'comparison', ?)""",
                                (word_id, error["correct"], json.dumps([error]))
                            )
                            added_rules += 1
            else:
                print(f"  Word not found: {english}")

        conn.commit()
        print(f"\nMigration completed!")
        print(f"  Words updated: {updated}")
        print(f"  Usage rules added: {added_rules}")

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
        print("Usage: python migrate_004_function_words.py [path_to_database]")
        sys.exit(1)

    migrate(db_path)
