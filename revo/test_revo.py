from utils import add_hats

def test_add_hats():
    assert add_hats('') == ''
    assert add_hats('saluton') == 'saluton'
    assert add_hats('sercxi') == 'serĉi'
    assert add_hats('CxSxGxJxHxUxcxsxgxjxhxux') == 'ĈŜĜĴĤŬĉŝĝĵĥŭ'
