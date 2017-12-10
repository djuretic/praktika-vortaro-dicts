from process_revo import get_main_word, stringify_children, parse_snc
import xml.etree.ElementTree as ET


def test_mrk():
    assert get_main_word('amik.0o') == 'amiko'


def test_mrk_suffix():
    assert get_main_word('lob.tri0ulo.PAL') == 'trilobulo'


def test_stringify_xml():
    assert 'Hola' == stringify_children(ET.fromstring('<a>   Hola  </a>'))
    assert '<b>Ho</b>la' == stringify_children(ET.fromstring('<a><b>Ho</b>la</a>'))


def test_stringify_xml_newlines():
    assert '<b>Saluton</b>mondo' == stringify_children(ET.fromstring("<i>\n<b>Saluton\n</b>mon\ndo</i>"))


def test_stringify_xml_whitespace():
    assert 'Bonan tagon' == stringify_children(ET.fromstring('<a>Bonan    tagon</a>'))


def test_snc():
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert 'ARKI Supera plata parto de kolona <ref cel="kapite.0o" tip="vid">kapitelo</ref>.' == parse_snc(ET.fromstring(xml), None)


def test_snc_replace_tld():
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert 'Monaĥejestro de abatejo.' == parse_snc(ET.fromstring(xml), None)


def test_snc_no_tail_after_tld():
    assert 'abat' == parse_snc(ET.fromstring('<snc mrk="abat.0o"><dif><tld/></dif></snc>'), None)
