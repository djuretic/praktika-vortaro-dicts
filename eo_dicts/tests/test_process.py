import sys
import os
import functools
import sqlite3
from click.testing import CliRunner
import pytest
from ..process_revo import main
from ..utils import output_dir

TEST_DB = 'test.db'


# source: https://github.com/pallets/click/issues/737#issuecomment-309231467
@pytest.fixture
def runner():
    """Yield a click.testing.CliRunner to invoke the CLI."""
    class_ = CliRunner

    def invoke_wrapper(f):
        """Augment CliRunner.invoke to emit its output to stdout.

        This enables pytest to show the output in its logs on test
        failures.
        """
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            sys.stdout.write(result.output)
            return result
        return wrapper

    class_.invoke = invoke_wrapper(class_.invoke)
    cli_runner = class_()
    yield cli_runner


def db_file():
    return os.path.join(output_dir(), TEST_DB)


def test_process_subart(runner):
    result = runner.invoke(main, ['--output-db', TEST_DB, '--xml-file', '/src/revo/xml/an.xml'])
    assert result.exit_code == 0

    conn = sqlite3.connect(db_file())
    cursor = conn.cursor()
    res = cursor.execute("SELECT words, mark, position from definitions")
    assert list(res) == [
        ('-an', 'an.0', 1),
        ('anaro', 'an.0aro', 3),
        ('aniĝi', 'an.0igxi', 4),
        ('ano', 'an.0o', 2)
    ]


def test_process_subart_2(runner):
    result = runner.invoke(main, ['--output-db', TEST_DB, '--xml-file', '/src/revo/xml/al.xml'])
    assert result.exit_code == 0

    conn = sqlite3.connect(db_file())
    cursor = conn.cursor()
    res = cursor.execute("SELECT word, definition_id from words")
    assert list(res) == [
        ('al', 1),
        ('alaĵo', 2),
        ('aligi', 3),
        ('aliĝi', 4),
        ('aliĝilo', 5),
    ]
