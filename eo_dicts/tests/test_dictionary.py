from ..parser.dictionary import DictionaryParser
import sqlite3
import pytest

output_path = "/tmp/test.db"

def test_single_entry_with_target_lang():
    DictionaryParser.parse_string("a: b", source_lang="eo", target_lang="es", output_db=output_path, output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'a', 'b')

def test_single_entry_with_source_lang():
    DictionaryParser.parse_string("a: b", source_lang="es", target_lang="eo", output_db=output_path, output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'b', 'a')

def test_skip_header():
    DictionaryParser.parse_string("Saluton:\nc: d", source_lang="eo", target_lang="es", output_db=output_path, output_table="eo_test", header_lines=1)
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT id, eo, es FROM eo_test")
    assert cursor.fetchone() == (1, 'c', 'd')

def test_skip_blank_lines():
    DictionaryParser.parse_string("  \n\n", source_lang="eo", target_lang="es", output_db=output_path, output_table="eo_test")
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) from eo_test")
    assert cursor.fetchone()[0] == 0
