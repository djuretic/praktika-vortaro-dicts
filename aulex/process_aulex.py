import html2text
import os
import sqlite3

def process_row(row, cursor):
    if ":" not in row:
        return
    esperanto, english = row.split(':')
    print(repr(esperanto), repr(english))
    cursor.execute(
        "INSERT INTO aulex (eo, es) VALUES (?, ?)",
        (esperanto.strip(), english.strip()))


def create_db(output_db):
    base_dir = os.path.dirname(__file__)
    db_filename = os.path.join(base_dir, output_db)
    try:
        os.remove(db_filename)
    except:
        pass
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE aulex (
            id integer primary key,
            eo text,
            es text
        )
    """)
    return conn


def main():
    conn = create_db(os.path.join(os.path.dirname(__file__), '..', 'output', 'aulex.db'))
    cursor = conn.cursor()
    with open('eo-es.htm') as f:
        for n, row in enumerate(html2text.html2text(f.read()).splitlines()):
            if n <= 2:
                continue
            process_row(row, cursor)
    cursor.execute("CREATE INDEX index_eo_aulex ON aulex (eo)")
    cursor.execute("CREATE INDEX index_es_aulex ON aulex (es)")
    conn.commit()
    cursor.close()


if __name__ == '__main__':
    main()
