import os
import sqlite3

def create_db(output_db, output_table, target_lang):
    base_dir = os.path.dirname(__file__)
    db_filename = os.path.join(base_dir, output_db)
    try:
        os.remove(db_filename)
    except:
        pass
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE {table} (
            id integer primary key,
            eo text,
            {lang} text
        )
    """.format(table=output_table, lang=target_lang))
    return conn

def process_row(row, cursor, output_table, target_lang, separator=":"):
    if separator not in row:
        return
    parts = row.split(separator, maxsplit=1)
    parts = [s.strip() for s in parts]
    print(repr(parts))
    cursor.execute(
        "INSERT INTO {table} (eo, {lang}) VALUES (?, ?)".format(table=output_table, lang=target_lang),
        (parts[0], parts[1]))


class DictionaryParser:
    @classmethod
    def parse_string(cls, input_string, target_lang, output_db, output_table, header_lines=0):
        conn = create_db(output_db, output_table, target_lang)
        cursor = conn.cursor()

        for n, row in enumerate(input_string.splitlines()):
            if n < header_lines:
                continue
            process_row(row, cursor, output_table, target_lang)
        cursor.execute("CREATE INDEX index_eo_espdic ON {table} (eo)".format(table=output_table))
        cursor.execute("CREATE INDEX index_{lang}_espdic ON {table} ({lang})".format(table=output_table, lang=target_lang))
        conn.commit()
        cursor.close()
