import os
import sqlite3

def process_row(row, cursor):
    if ":" not in row:
        return
    esperanto, english = row.split(' : ')
    print(repr(esperanto), repr(english))
    cursor.execute(
        "INSERT INTO espdic (eo, en) VALUES (?, ?)",
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
        CREATE TABLE espdic (
            id integer primary key,
            eo text,
            en text
        )
    """)
    return conn


def main():
    conn = create_db(os.path.join(os.path.dirname(__file__), '..', 'output', 'espdic.db'))
    cursor = conn.cursor()
    with open('espdic.txt') as f:
        for n, row in enumerate(f.readlines()):
            if n == 0:
                continue
            process_row(row, cursor)
    cursor.execute("CREATE INDEX index_eo_espdic ON espdic (eo)")
    cursor.execute("CREATE INDEX index_en_espdic ON espdic (en)")
    conn.commit()
    cursor.close()



if __name__ == '__main__':
    main()