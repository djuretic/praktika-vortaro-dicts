import sqlite3
import os
from .utils import output_dir


def search_multiple(*words: str) -> None:
    for word in words:
        search(word)


def search(word: str) -> None:
    db_filename = os.path.join(output_dir(), "vortaro.db")
    conn = sqlite3.connect(db_filename)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        for row in cursor.execute(
            """
                SELECT *
                FROM words w
                LEFT JOIN definitions d ON (w.definition_id = d.id)
                WHERE word = ?
                """,
            (word,),
        ):
            for field, value in dict(row).items():
                print("%s: %s" % (field, repr(value)))
            print("")
    finally:
        cursor.close()
        conn.close()


def stats() -> None:
    db_filename = os.path.join(output_dir(), "vortaro.db")
    conn = sqlite3.connect(db_filename)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM version")
        print("Version:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM words")
        print("Words:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM definitions")
        print("Definitions:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM languages")
        print("Languages:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM translations_es")
        translations_es = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM translations_en")
        translations_en = cursor.fetchone()[0]
        print("Translations:")
        print("\tEnglish:", translations_en)
        print("\tSpanish:", translations_es)
    finally:
        cursor.close()
        conn.close()
