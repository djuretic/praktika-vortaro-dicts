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
