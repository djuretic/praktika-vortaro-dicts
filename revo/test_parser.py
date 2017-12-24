from parser.revo import Art, Snc
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


def test_subsnc():
    xml = '''<snc mrk="-">
        <dif>Uzata kiel:</dif>
        <subsnc><dif>A</dif></subsnc>
        <subsnc><dif>B</dif></subsnc>
    </snc>'''
    assert Snc(etree.fromstring(xml)).to_text() == "Uzata kiel:\n\na) A\n\nb) B"

def test_multiple_snc():
    xml = '''<art>
        <kap><rad>zon</rad>/o</kap>
        <drv mrk="zon.0o">
            <kap><ofc>*</ofc><tld/>o</kap>
            <snc mrk="zon.0o.TEKS"><dif>A</dif></snc>
            <snc mrk="zon.0o.korpo"><dif>B</dif></snc>
        </drv>
    </art>
    '''
    assert Art(etree.fromstring(xml)).to_text() == "1. A\n\n2. B"