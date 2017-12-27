from process_revo import get_main_word
from utils import add_hats


def test_mrk():
    assert get_main_word('amik', 'amik.0o') == 'amiko'
    # Note that the second one is aberac and not aberaci
    assert get_main_word('aberaci', 'aberac.0i.SCI') == 'aberacii'


def test_mrk_suffix():
    assert get_main_word('lob', 'lob.tri0ulo.PAL') == 'trilobulo'


def test_mrk_uppercase():
    assert get_main_word('germani', 'germani.G0o') == 'Germanio'
    assert get_main_word('gxibuti', 'gxibuti.GX0o') == 'Ĝibutio'


def test_mrk_separation():
    assert get_main_word('alask', 'alask.A0aGolfo') == 'Alaska Golfo'


def test_add_hats():
    assert add_hats('') == ''
    assert add_hats('saluton') == 'saluton'
    assert add_hats('sercxi') == 'serĉi'
    assert add_hats('CxSxGxJxHxUxcxsxgxjxhxux') == 'ĈŜĜĴĤŬĉŝĝĵĥŭ'
