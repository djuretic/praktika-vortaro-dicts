import sqlite3
import click

@click.command()
@click.option('--word')
def search(word):
    db_filename = 'vortaro.db'
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    try:
        for row in cursor.execute("SELECT * FROM words WHERE word = ?", (word,)):
            for field in row:
                print(field)
    finally:
        cursor.close()
        conn.close()



if __name__ == '__main__':
    search()