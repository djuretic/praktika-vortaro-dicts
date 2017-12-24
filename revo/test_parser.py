from parser.revo import Snc
from lxml import etree
import pytest

@pytest.fixture()
def parser():
    return etree.XMLParser(remove_blank_text=True)

def test_snc(parser):
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert Snc(etree.fromstring(xml, parser=parser)).to_text() == 'ARKI Supera plata parto de kolona kapitelo.'


def test_snc_replace_tld(parser):
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert Snc(etree.fromstring(xml, parser=parser)).to_text() == 'Monaĥejestro de abatejo.'
