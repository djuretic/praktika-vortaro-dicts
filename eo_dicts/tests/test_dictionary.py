from ..parser.dictionary import DictionaryParser
import sqlite3
import pytest

output_path = "/tmp/test.db"

def test_single_entry():
    DictionaryParser.parse_string("a: b", target_lang="es", output_db=output_path, output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'a', 'b')

def test_skip_header():
    DictionaryParser.parse_string("Saluton:\nc: d", target_lang="es", output_db=output_path, output_table="eo_test", header_lines=1)
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'c', 'd')

def test_skip_blank_lines():
    DictionaryParser.parse_string("  \n\n", target_lang="es", output_db=output_path, output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 0
