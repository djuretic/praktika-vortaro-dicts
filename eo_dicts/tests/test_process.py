import sys
import functools
import sqlite3
from click.testing import CliRunner
import pytest
from ..process_revo import main

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


def test_process_subart(runner):
    result = runner.invoke(main, ['--output-db', TEST_DB, '--xml-file', '/src/revo/xml/gx.xml'])
    assert result.exit_code == 0

    conn = sqlite3.connect('eo_dicts/' + TEST_DB)
    cursor = conn.cursor()
    res = cursor.execute("SELECT word, mark, article_id, position from words")
    assert list(res) == [
        ('ĝ', 'gx.0.konsonanto', 1, 1),
        ('ĝo', 'gx.0.nomo', 1, 2),
    ]

def test_process_subart_2(runner):
    result = runner.invoke(main, ['--output-db', TEST_DB, '--xml-file', '/src/revo/xml/al.xml'])
    assert result.exit_code == 0

    conn = sqlite3.connect('eo_dicts/' + TEST_DB)
    cursor = conn.cursor()
    res = cursor.execute("SELECT word, article_id from words")
    assert list(res) == [
        ('al', 1),
        ('alaĵo', 1),
        ('aligi', 1),
        ('aliĝi', 1),
        ('aliĝilo', 1),
    ]
