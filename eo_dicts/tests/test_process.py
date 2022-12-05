import os
import sqlite3
import pytest
from ..utils import output_dir
from ..cli import Vortaro

TEST_DB = "test.db"
XML_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "revo", "xml")


# source: https://github.com/pallets/click/issues/737#issuecomment-309231467
@pytest.fixture
def vortaro():
    return Vortaro()


def db_file():
    return os.path.join(output_dir(), TEST_DB)


def test_process_subart(vortaro):
    vortaro.process_revo(
        output_db=TEST_DB, xml_file=os.path.join(XML_BASE_DIR, "an.xml")
    )

    conn = sqlite3.connect(db_file())
    cursor = conn.cursor()
    res = cursor.execute("SELECT words, mark, position from definitions")
    assert list(res) == [
        ("-an", "an.0", 1),
        ("anaro", "an.0aro", 3),
        ("aniĝi", "an.0igxi", 4),
        ("ano", "an.0o", 2),
    ]


def test_process_subart_2(vortaro):
    vortaro.process_revo(
        output_db=TEST_DB, xml_file=os.path.join(XML_BASE_DIR, "al.xml")
    )

    conn = sqlite3.connect(db_file())
    cursor = conn.cursor()
    res = cursor.execute("SELECT word, definition_id from words")
    assert list(res) == [
        ("al", 1),
        ("aligi", 2),
        ("aliĝi", 3),
        ("aliĝilo", 4),
        ("malaliĝi", 5),
        ("realiĝi", 6),
    ]
