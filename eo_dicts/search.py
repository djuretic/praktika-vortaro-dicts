import sqlite3
import click
import os

@click.command()
@click.option('--word')
def search(word):
    db_filename = os.path.join(os.path.dirname(__file__), 'vortaro.db')
    conn = sqlite3.connect(db_filename)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        for row in cursor.execute("""
            SELECT *
            FROM words w
            LEFT JOIN definitions d ON (w.definition_id = d.id)
            WHERE word = ?
            """, (word,)):
            for field, value in dict(row).items():
                print("%s: %s" % (field, repr(value)))
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    search()
