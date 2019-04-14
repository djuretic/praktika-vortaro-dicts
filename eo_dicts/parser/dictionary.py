import os
import sqlite3

class DictionaryParser:
    @classmethod
    def parse_string(cls, input_string, target_lang, output_db, output_table, header_lines=0):
        parser = cls(target_lang, output_db, output_table, header_lines)
        parser.parse(input_string.splitlines())

    @classmethod
    def parse_file(cls, input_filename, target_lang, output_db, output_table, header_lines=0):
        parser = cls(target_lang, output_db, output_table, header_lines)
        with open(input_filename) as f:
            parser.parse(f.readlines())

    def __init__(self, target_lang, output_db, output_table, header_lines):
        self.target_lang = target_lang
        self.output_db = output_db
        self.output_table = output_table
        self.header_lines = header_lines

    def create_db(self):
        db_filename = self.output_db
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
        """.format(table=self.output_table, lang=self.target_lang))
        return conn

    def parse(self, generator):
        conn = self.create_db()
        cursor = conn.cursor()

        for n, row in enumerate(generator):
            if n < self.header_lines:
                continue
            self.process_row(row, cursor)
        cursor.execute("CREATE INDEX index_eo_espdic ON {table} (eo)".format(table=self.output_table))
        cursor.execute("CREATE INDEX index_{lang}_espdic ON {table} ({lang})".format(table=self.output_table, lang=self.target_lang))
        conn.commit()
        cursor.close()

    def process_row(self, row, cursor, separator=":"):
        if separator not in row:
            return
        parts = row.split(separator, maxsplit=1)
        parts = [s.strip() for s in parts]
        print(repr(parts))
        cursor.execute(
            "INSERT INTO {table} (eo, {lang}) VALUES (?, ?)".format(table=self.output_table, lang=self.target_lang),
            (parts[0], parts[1]))
