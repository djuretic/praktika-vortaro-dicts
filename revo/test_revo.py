from process_revo import get_main_word
from utils import add_hats


def test_mrk():
    assert get_main_word('amik.0o') == 'amiko'


def test_mrk_suffix():
    assert get_main_word('lob.tri0ulo.PAL') == 'trilobulo'


def test_mrk_uppercase():
    assert get_main_word('germani.G0o') == 'Germanio'
    assert get_main_word('gxibuti.GX0o') == 'Ĝibutio'


def test_mrk_separation():
    assert get_main_word('alask.A0aGolfo') == 'Alaska Golfo'


def test_add_hats():
    assert add_hats('') == ''
    assert add_hats('saluton') == 'saluton'
    assert add_hats('sercxi') == 'serĉi'
    assert add_hats('CxSxGxJxHxUxcxsxgxjxhxux') == 'ĈŜĜĴĤŬĉŝĝĵĥŭ'
