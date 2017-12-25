from parser.revo import Art, Snc
from lxml import etree
import pytest

def test_snc():
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert Snc(etree.fromstring(xml)).to_text() == 'ARKI Supera plata parto de kolona kapitelo.'


def test_snc_no_tail_after_tld():
    assert Snc(etree.fromstring('<snc mrk="abat.0o"><dif><tld/></dif></snc>')).to_text() == 'abat'


def test_snc_ignore_fnt():
    xml = '<snc mrk="-"><dif>Difino <ekz>Frazo<fnt><aut>Iu</aut></fnt>.</ekz></dif></snc>'
    assert Snc(etree.fromstring(xml)).to_text() == 'Difino Frazo.'


def test_snc_ignore_trd():
    xml = '<snc mrk="-"><dif>Difino <ekz><ind>Frazo</ind>.<trd lng="hu">Trd</trd></ekz></dif></snc>'
    assert Snc(etree.fromstring(xml)).to_text() == 'Difino Frazo.'

def test_snc_replace_tld():
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert Snc(etree.fromstring(xml)).to_text() == 'Monaĥejestro de abatejo.'


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
    assert list(Art(etree.fromstring(xml)).derivations()) == ["1. A\n\n2. B"]