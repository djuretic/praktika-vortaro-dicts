from ..parser.revo import Art, Snc, Dif, Drv, Subart, Refgrp
from lxml import etree
import pytest


@pytest.fixture
def parser():
    return lambda xml: etree.fromstring(xml)


def test_set_parent(parser):
    xml = """<art>
    <kap>-<rad>aĉ</rad>/</kap>
    <subart>
        <drv><kap>-<tld/></kap></drv>
    </subart>
    </art>"""
    art = Art(parser(xml))
    for tag in art.children:
        assert tag.parent == art


def test_article_kap(parser):
    xml = """<art>
        <kap>
            <ofc>1</ofc>
            -<rad>aĉ</rad>/ <fnt><bib>PV</bib></fnt>
        </kap>
    </art>"""
    assert Art(parser(xml)).kap == ("aĉ", "/")


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
    assert derivs[0].__class__ is Subart
    parsed = derivs[0].to_text()
    assert (
        parsed.string == "Prefikso kun la senco al: \nalveni, alkuri alporti, alesti."
    )
    assert parsed.format == {
        "ekz": [(27, 58)],
        "tld": [(27, 29), (35, 37), (42, 44), (51, 53)],
    }


def test_drv_multiple_kap(parser):
    xml = """<drv mrk="ajn.sen0a"><kap>sen <tld/>a, <var><kap>sen ia <tld/></kap></var></kap></drv>"""
    assert Drv(parser(xml), {"radix": "ajn"}).kap == "sen ajna, sen ia ajn"


def test_drv_kap(parser):
    xml = '<drv mrk="a1.0.volvita"><kap><tld/> volvita</kap></drv>'
    assert Drv(parser(xml), {"radix": "a"}).kap == "a volvita"


def test_drv_main_word_multiple(parser):
    xml = '<drv mrk="abort.0ajxo"><kap><tld/>aĵo, <var><kap><tld/>ulo</kap></var></kap></drv>'
    assert Drv(parser(xml), {"radix": "abort"}).main_word() == "abortaĵo, abortulo"


def test_drv_whitespace_after_gra_and_ref(parser):
    xml = """<drv mrk="abol.0i">
        <kap><tld/>i</kap>
        <gra><vspec>tr</vspec></gra>
        <snc mrk="abol.0i.JUR">
            <uzo tip="fak">JUR</uzo>
            <ref tip="dif" cel="abolic.0i">abolicii</ref>
            <ekz>
            sklaveco estis <tld/>ita en Brazilo en 1888.
            </ekz>
        </snc>
    </drv>"""
    assert (
        Drv(parser(xml), {"radix": "abol"}).to_text().string
        == "(tr) JUR = abolicii \nsklaveco estis abolita en Brazilo en 1888. "
    )


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
    assert (
        Drv(parser(xml), {"radix": "ad"}).to_text().string
        == "Sufikso esprimanta ĝenerale la agon kaj uzata por derivi:\n\nA. substantivojn: "
    )


def test_subdrv_snc(parser):
    xml = """<drv mrk="ir.0ado">
        <kap><tld/>ado, <var><kap><tld/>o</kap></var></kap>
        <subdrv>
            <dif>
            Ago <tld/>i:
            </dif>
            <snc mrk="ir.0ado.deAL"><ekz>Frazo</ekz></snc>
            <snc mrk="ir.0ado.al"><ekz>Alia frazo</ekz></snc>
        </subdrv>
        <subdrv><dif>Maniero (...)</dif></subdrv>
    </drv>
    """
    assert (
        Drv(parser(xml), {"radix": "ir"}).to_text().string
        == "A. Ago iri: \n\n1. \nFrazo\n\n2. \nAlia frazo\n\nB. Maniero (...)"
    )


def test_snc_single(parser):
    xml = """<snc mrk="abak.0o.ARKI">
    <uzo tip="fak">ARKI</uzo>
    <dif>
      Supera plata parto de kolona
      <ref tip="vid" cel="kapite.0o">kapitelo</ref>.
    </dif>
    </snc>"""
    assert (
        Snc(parser(xml)).to_text().string
        == "ARKI Supera plata parto de kolona kapitelo. "
    )


def test_snc_no_tail_after_tld(parser):
    assert (
        Snc(parser('<snc mrk="abat.0o"><dif><tld/></dif></snc>'), {"radix": "abat"})
        .to_text()
        .string
        == "abat"
    )


def test_snc_ignore_fnt(parser):
    xml = (
        '<snc mrk="-"><dif>Difino <ekz>Frazo<fnt><aut>Iu</aut></fnt>.</ekz></dif></snc>'
    )
    assert Snc(parser(xml)).to_text().string == "Difino \nFrazo."


def test_snc_ignore_trd(parser):
    xml = '<snc mrk="-"><dif>Difino <ekz><ind>Frazo</ind>.<trd lng="hu">Trd</trd></ekz></dif></snc>'
    tag = Snc(parser(xml)).to_text()
    assert tag.string == "Difino \nFrazo."
    assert tag.format == {"ekz": [(8, 14)]}


def test_snc_replace_tld(parser):
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld/>ejo.</dif>
    </snc>"""
    assert (
        Snc(parser(xml), {"radix": "abat"}).to_text().string
        == "Monaĥejestro de abatejo."
    )


def test_snc_replace_tld_lit(parser):
    xml = """<snc mrk="abat.0o">
    <dif>Monaĥejestro de <tld lit="A"/>ejo.</dif>
    </snc>"""
    assert (
        Snc(parser(xml), {"radix": "abat"}).to_text().string
        == "Monaĥejestro de Abatejo."
    )


def test_snc_whitespace(parser):
    xml = """<snc>
    <dif>
        Amata:
        <ekz>
            <tld/>a patrino;
        </ekz>
        <ekz>
            nia <ind><tld/>memora</ind> majstro
        </ekz>
    </dif></snc>
    """
    assert (
        Snc(parser(xml), {"radix": "kar"}).to_text().string
        == "Amata: \nkara patrino; \nnia karmemora majstro "
    )


def test_snc_no_more_whitespace_after_ref(parser):
    xml = """<snc>
        <dif>
            <ref tip="lst" cel="famili.0o.BIO"
                lst="voko:zoologiaj_familioj">Familio</ref> el la ordo
            <ref tip="malprt" cel="best.rabo0oj">rabobestoj</ref>
            (<trd lng="la">Canidae</trd>).
        </dif>
    </snc>"""
    assert (
        Snc(parser(xml), {"radix": "hunded"}).to_text().string
        == "Familio el la ordo rabobestoj (Canidae). "
    )


def test_subsnc(parser):
    xml = """<snc mrk="-">
        <dif>Uzata kiel:</dif>
        <subsnc><dif>A</dif></subsnc>
        <subsnc><dif>B</dif></subsnc>
    </snc>"""
    assert Snc(parser(xml)).to_text().string == "Uzata kiel:\n\na) A\n\nb) B"


def test_multiple_snc(parser):
    xml = """<art>
        <kap><rad>zon</rad>/o</kap>
        <drv mrk="zon.0o">
            <kap><ofc>*</ofc><tld/>o</kap>
            <snc mrk="zon.0o.TEKS"><dif>A</dif></snc>
            <snc mrk="zon.0o.korpo"><dif>B</dif></snc>
        </drv>
    </art>
    """
    drvs = [d.to_text().string for d in Art(parser(xml)).derivations()]
    assert drvs == ["1. A\n\n2. B"]


def test_dif_space_between_elements(parser):
    xml = """<dif>
            <ref tip="dif" cel="fin.0ajxo.GRA">Finaĵo</ref>
            (lingvoscience: sufikso)
        </dif>"""
    assert Dif(parser(xml)).to_text().string == "Finaĵo (lingvoscience: sufikso) "


def test_trd_inside_ekz(parser):
    xml = """<art>
        <kap><rad>abstin</rad>/i</kap>
        <drv mrk="abstin.0i">
            <kap><tld/>i</kap>
            <gra><vspec>ntr</vspec></gra>
            <snc>
                <dif>Trinki ion pro medicina motivo:
                    <ekz>
                        <ind><tld/>ulo</ind>;
                        <trd lng="ca">abstinent<klr> (subst.)</klr></trd>
                        <trdgrp lng="hu">
                            <trd>absztinens</trd>,
                            <trd>önmegtartóztatás;</trd>
                        </trdgrp>
                        <trd lng="es">abstemio</trd>
                    </ekz>
                </dif>
            </snc>
            <trd lng="en">abstain</trd>
        </drv>
    </art>"""
    derivs = list(Art(parser(xml)).derivations())
    assert len(derivs) == 1
    trds = derivs[0].translations()
    assert trds == {
        "abstini": {"en": {None: ["abstain"]}},
        # 'abstinulo': {
        #     'ca': ['abstinent (subst.)'],
        #     'hu': ['absztinens', 'önmegtartóztatás'],
        #     'es': ['abstemio']},
    }


def test_trd_preserves_whitespace(parser):
    # pl words come from abdiki
    xml = """<drv mrk="telefo.posx0o">
        <kap>poŝ<tld/>o</kap>
        <trdgrp lng="es">
            <trd><klr tip="amb">teléfono</klr> <ind>móvil</ind></trd>,
            <trd><klr tip="amb">teléfono</klr> <ind>celular</ind></trd>
        </trdgrp>
        <trdgrp lng="pl">
           <trd><klr>dać </klr>dymisję</trd>
        </trdgrp>
    </drv>"""
    drv = Drv(parser(xml), {"radix": "telefon"})
    trds = drv.translations()
    assert trds == {
        "poŝtelefono": {
            "es": {None: ["teléfono móvil", "teléfono celular"]},
            "pl": {None: ["dać dymisję"]},
        }
    }


def test_trd_inside_snc(parser):
    xml = """<drv mrk="brik.0o">
        <kap><ofc>*</ofc><tld/>o</kap>
        <snc mrk="brik.0o.bakita">
            <trd lng="en">brick</trd>
        </snc>
        <snc mrk="brik.0o.FIG_elemento"></snc>
        <snc mrk="brik.0o.formo">
            <trd lng="en">block</trd>
        </snc>
    </drv>"""
    drv = Drv(parser(xml), {"radix": "brik"})
    trds = drv.translations()
    assert trds == {"briko": {"en": {1: ["brick"], 3: ["block"]}}}


def test_trd_inside_only_snc(parser):
    xml = """<drv mrk="cxili.CX0o">
        <kap><tld/>o</kap>
        <snc><trd lng="da">Chile</trd></snc>
    </drv>"""
    drv = Drv(parser(xml), {"radix": "cxili"})
    assert drv.translations() == {"ĉilio": {"da": {None: ["Chile"]}}}


def test_trd_multiple_kap(parser):
    xml = """<drv mrk="arab.SaudaA0ujo">
        <kap>Sauda <tld lit="A"/>ujo,
            <var><kap>Saud-<tld lit="A"/>ujo</kap></var>,
            <var><kap>Saŭda <tld lit="A"/>ujo</kap></var>
        </kap>
        <trd lng="pl">Arabia Saudyjska</trd>
    </drv>"""
    drv = Drv(parser(xml), {"radix": "arab"})
    assert drv.translations() == {
        "Sauda Arabujo, Saud-Arabujo, Saŭda Arabujo": {
            "pl": {None: ["Arabia Saudyjska"]}
        }
    }


def test_refgrp_arrow(parser):
    xml = """<refgrp tip="sin">
        <ref cel="plagx.0o">plaĝo</ref>
    </refgrp>"""
    assert Refgrp(parser(xml)).to_text().string == "→ plaĝo"
