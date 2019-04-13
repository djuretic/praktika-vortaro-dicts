from ..parser.dictionary import DictionaryParser
import sqlite3
import pytest

def test_single_entry():
    output_path = "/tmp/test.db"
    DictionaryParser.parse_string("a: b", target_lang="es", output_db="/tmp/test.db", output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'a', 'b')