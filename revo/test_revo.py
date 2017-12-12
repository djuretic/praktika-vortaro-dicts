from process_revo import get_main_word, stringify_children, parse_snc
from utils import add_hats
import xml.etree.ElementTree as ET


def test_mrk():
    assert get_main_word('amik.0o') == 'amiko'


def test_mrk_suffix():
    assert get_main_word('lob.tri0ulo.PAL') == 'trilobulo'


def test_mrk_uppercase():
    assert get_main_word('germani.G0o') == 'Germanio'
    assert get_main_word('gxibuti.GX0o') == 'Ĝibutio'


def test_mrk_separation():
    assert get_main_word('alask.A0aGolfo') == 'Alaska Golfo'


def test_stringify_xml():
    assert stringify_children(ET.fromstring('<a>   Hola  </a>')) == 'Hola'
    assert stringify_children(ET.fromstring('<a><b>Ho</b>la</a>')) == 'Hola'


def test_stringify_xml_newlines():
    assert stringify_children(ET.fromstring("<i>\n<b>Saluton\n</b> mon\ndo</i>")) == \
        'Saluton mondo'


def test_stringify_xml_whitespace():
    assert stringify_children(ET.fromstring('<a>Bonan    tagon</a>')) == 'Bonan tagon'


def test_snc():
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert parse_snc(ET.fromstring(xml), None) == 'ARKI Supera plata parto de kolona kapitelo.'


def test_snc_replace_tld():
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert parse_snc(ET.fromstring(xml), None) == 'Monaĥejestro de abatejo.'


def test_snc_no_tail_after_tld():
    assert parse_snc(ET.fromstring('<snc mrk="abat.0o"><dif><tld/></dif></snc>'), None) == 'abat'


def test_snc_ignore_fnt():
    xml = '<snc mrk="-"><dif>Difino <ekz>Frazo<fnt><aut>Iu</aut></fnt>.</ekz></dif></snc>'
    assert parse_snc(ET.fromstring(xml), None) == 'Difino Frazo.'


def test_add_hats():
    assert add_hats('') == ''
    assert add_hats('saluton') == 'saluton'
    assert add_hats('sercxi') == 'serĉi'
    assert add_hats('CxSxGxJxHxUxcxsxgxjxhxux') == 'ĈŜĜĴĤŬĉŝĝĵĥŭ'
