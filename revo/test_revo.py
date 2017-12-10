from process_revo import get_main_word, stringify_children
import xml.etree.ElementTree as ET


def test_mrk():
    assert get_main_word('amik.0o') == 'amiko'


def test_mrk_suffix():
    assert get_main_word('lob.tri0ulo.PAL') == 'trilobulo'


def test_string_xml():
    assert 'Hola' == stringify_children(ET.fromstring('<a>   Hola  </a>'))
    assert '<b>Ho</b>la' == stringify_children(ET.fromstring('<a><b>Ho</b>la</a>'))
