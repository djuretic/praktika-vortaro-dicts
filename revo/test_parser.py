from parser.revo import Art, Snc, Dif, Drv
from lxml import etree
import pytest

@pytest.fixture
def parser():
    return lambda xml:  etree.fromstring(xml)

def test_article_kap(parser):
    xml = """<art>
        <kap>
            <ofc>1</ofc>
            -<rad>aĉ</rad>/ <fnt><bib>PV</bib></fnt>
        </kap>
    </art>"""
    assert Art(parser(xml)).kap == ('aĉ', '/')

def test_article_no_drv(parser):
    xml = """<art>
        <kap><rad>al</rad></kap>
        <subart>
            <dif>Prefikso kun la senco <tld/><sncref ref="al.0.prep_proksimigxo"/></dif>:
            <snc ref="al.0.prep_proksimigxo">
                <ekz><ind><tld/>veni</ind>, <tld/>kuri <tld/>porti, <tld/>esti.</ekz>
            </snc>
        </subart>
    </art>"""
    derivs = list(Art(parser(xml)).derivations())
    assert len(derivs) == 1
    assert derivs[0].to_text() == 'Prefikso kun la senco al: alveni, alkuri alporti, alesti.'

def test_drv_multiple_kap(parser):
    xml = """<drv mrk="ajn.sen0a"><kap>sen <tld/>a, <var><kap>sen ia <tld/></kap></var></kap></drv>"""
    assert Drv(parser(xml), {'radix': 'ajn'}).kap == 'sen ajna, sen ia ajn'

def test_subdrv(parser):
    xml = """<drv mrk="ad.0">
        <kap><ofc>*</ofc>-<tld/></kap>
        <dif>Sufikso esprimanta ĝenerale la agon kaj uzata por derivi:</dif>
        <subdrv>
            <dif>
                substantivojn:
            </dif>
        </subdrv>
    </drv>"""
    assert Drv(parser(xml), {'radix': 'ad'}).to_text() == "Sufikso esprimanta ĝenerale la agon kaj uzata por derivi: \n\nA. substantivojn:"

def test_snc(parser):
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert Snc(parser(xml)).to_text() == 'ARKI Supera plata parto de kolona → kapitelo.'


def test_snc_no_tail_after_tld(parser):
    assert Snc(parser('<snc mrk="abat.0o"><dif><tld/></dif></snc>'), {"radix": "abat"}).to_text() == 'abat'


def test_snc_ignore_fnt(parser):
    xml = '<snc mrk="-"><dif>Difino <ekz>Frazo<fnt><aut>Iu</aut></fnt>.</ekz></dif></snc>'
    assert Snc(parser(xml)).to_text() == 'Difino Frazo.'


def test_snc_ignore_trd(parser):
    xml = '<snc mrk="-"><dif>Difino <ekz><ind>Frazo</ind>.<trd lng="hu">Trd</trd></ekz></dif></snc>'
    assert Snc(parser(xml)).to_text() == 'Difino Frazo.'

def test_snc_replace_tld(parser):
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert Snc(parser(xml), {"radix": "abat"}).to_text() == 'Monaĥejestro de abatejo.'


def test_subsnc(parser):
    xml = '''<snc mrk="-">
        <dif>Uzata kiel:</dif>
        <subsnc><dif>A</dif></subsnc>
        <subsnc><dif>B</dif></subsnc>
    </snc>'''
    assert Snc(parser(xml)).to_text() == "Uzata kiel:\n\na) A\n\nb) B"

def test_multiple_snc(parser):
    xml = '''<art>
        <kap><rad>zon</rad>/o</kap>
        <drv mrk="zon.0o">
            <kap><ofc>*</ofc><tld/>o</kap>
            <snc mrk="zon.0o.TEKS"><dif>A</dif></snc>
            <snc mrk="zon.0o.korpo"><dif>B</dif></snc>
        </drv>
    </art>
    '''
    drvs = [d.to_text() for d in Art(parser(xml)).derivations()]
    assert drvs == ["1. A\n\n2. B"]

def test_dif_space_between_elements(parser):
    xml = '''<dif>
            <ref tip="dif" cel="fin.0ajxo.GRA">Finaĵo</ref>
            (lingvoscience: sufikso)
        </dif>'''
    assert Dif(parser(xml)).to_text() == "→ Finaĵo (lingvoscience: sufikso)"