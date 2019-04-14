import os
import sqlite3

class DictionaryParser:
    @classmethod
    def parse_string(cls, input_string, source_lang, target_lang, output_db, output_table, header_lines=0):
        parser = cls(source_lang, target_lang, output_db, output_table, header_lines)
        parser.parse(input_string.splitlines())

    @classmethod
    def parse_file(cls, input_filename, source_lang, target_lang, output_db, output_table, header_lines=0):
        parser = cls(target_lang, output_db, output_table, header_lines)
        with open(input_filename) as f:
            parser.parse(f.readlines())

    def __init__(self, source_lang, target_lang, output_db, output_table, header_lines):
        self.source_lang = source_lang
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
                {source_lang} text,
                {target_lang} text
            )
        """.format(table=self.output_table, source_lang=self.source_lang, target_lang=self.target_lang))
        return conn

    def parse(self, generator):
        conn = self.create_db()
        cursor = conn.cursor()

        for n, row in enumerate(generator):
            if n < self.header_lines:
                continue
            row = row.strip()
            if not row:
                continue
            # print(repr([n, row]))
            self.process_row(row, cursor)
        cursor.execute("CREATE INDEX index_{source_lang}_{table} ON {table} ({source_lang})".format(source_lang=self.source_lang, table=self.output_table))
        cursor.execute("CREATE INDEX index_{target_lang}_{table} ON {table} ({target_lang})".format(table=self.output_table, target_lang=self.target_lang))
        conn.commit()
        cursor.close()

    def process_row(self, row, cursor, separator=":"):
        if separator not in row:
            return
        parts = row.split(separator, maxsplit=1)
        parts = [s.strip() for s in parts]
        print(repr(parts))
        cursor.execute(
            "INSERT INTO {table} ({source_lang}, {target_lang}) VALUES (?, ?)".format(table=self.output_table, source_lang=self.source_lang, target_lang=self.target_lang),
            (parts[0], parts[1]))
