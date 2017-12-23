import re
import sqlite3
import glob
import xml.etree.ElementTree as ET
from lxml import etree
import click

from utils import add_hats


def stringify_children(node, word=None, first=True, ignore=None):
    # print(node, "Word: ", word)
    if node is None:
        return ''
    s = node.text
    if s is None:
        s = ''
    if node.tag in ['adm', 'bld', 'fnt'] or (ignore and node.tag in ignore):
        # Ignore them
        s = ''
        if node.tail:
            s = node.tail
        return s
    elif node.tag == 'tld':
        # Replace with head word
        res = word or ''
        if node.tail:
            res += node.tail
        return res

    has_child = False
    for child in node:
        has_child = True
        s += stringify_children(child, word, first=False, ignore=ignore)

    if not has_child and node.tail:
        s += node.tail

    # print(node, "Word: ", word, "Res:", s)
    if first:
        return ' '.join(s.strip().replace("\n", "").split())
    return s


def extract_translations(node, mrk):
    trads = {}

    def read_translation(mrk, lng, trd):
        trd_txt = stringify_children(trd)
        # print(' ', mrk, lng, trd_txt)
        if lng not in trads:
            trads[lng] = []
        trads[lng].append(trd_txt)

    for trd in node.findall('trd'):
        read_translation(mrk, trd.get('lng'), trd)
    for trdgrp in node.findall('trdgrp'):
        for trd in trdgrp.findall('trd'):
            read_translation(mrk, trdgrp.get('lng'), trd)

    # print(trads)
    return trads


def insert_translations(word_id, trads, cursor):
    if not trads:
        return
    for lng, trad in trads.items():
        cursor.execute(
            "INSERT INTO translations (word_id, lng, translation) VALUES (?,?,?)",
            (word_id, lng, " ".join(trad))
        )


# https://github.com/sstangl/tuja-vortaro/blob/master/revo/convert-to-js.py
def entities_dict():
    entities = {}

    with open('dtd/vokosgn.dtd', 'rb') as f:
        dtd = etree.DTD(f)
        for entity in dtd.iterentities():
            entities[entity.name] = entity.content

    with open('dtd/vokomll.dtd', 'rb') as f:
        dtd = etree.DTD(f)
        for entity in dtd.iterentities():
            entities[entity.name] = entity.content
    return entities


def create_db():
    conn = sqlite3.connect('vortaro.db')
    c = conn.cursor()
    c.execute('DROP TABLE if exists words')
    c.execute("""
        CREATE TABLE words (
            id integer primary key,
            article_id integer,
            word text,
            mark text,
            definition text
        )
    """)

    c.execute('DROP TABLE if exists translations')
    c.execute("""
        CREATE TABLE translations (
            id integer primary key,
            word_id integer,
            lng text,
            translation text
        )
    """)
    c.close()
    return conn


def get_main_word(mrk):
    mrk = add_hats(mrk)
    parts = mrk.split('.')
    pos = parts[1].index('0')

    if pos and parts[1][pos-1].isupper():
        parts[0] = parts[0].capitalize()
        word = re.sub('.0', parts[0], parts[1])
    else:
        word = parts[1].replace('0', parts[0])
    return re.sub(r"(\w)([A-ZĈŜĜĤĴ])", r"\1 \2", word)


def parse_article(filename, num_article, cursor, verbose=False):
    with open(filename) as f:
        article = f.read()

    xml_parser = ET.XMLParser()
    for entity, value in entities_dict().items():
        xml_parser.entity[entity] = value
    tree = ET.fromstring(article, parser=xml_parser)

    art = tree.find('art')
    main_word = art.find('kap/rad')
    if verbose:
        print(main_word)

    row_id = None
    found_words = []
    # TODO parse ref (ekz. a1)
    for drv in art.findall('drv'):
        # Example: afekcii has <dif> here
        meanings = []
        dif = drv.find('dif')
        mrk = drv.get('mrk')
        main_word_txt = get_main_word(mrk)
        found_words.append(main_word_txt)
        if dif is not None:
            meanings.append(stringify_children(dif))
        # TODO initial
        # word = drv.find('kap')
        # print(word.find('tld').tail)

        # TODO drv also has dif
        # parse multiple uzo (example: a1.xml)
        uzo_list = [t.text for t in drv.findall('uzo')]
        uzo_txt = ''
        if uzo_list:
            uzo_txt = " ".join(uzo_list) + " "

        for snc in drv.findall('snc'):
            meanings.append(uzo_txt + parse_snc(snc, drv, verbose)[0])

        if len(meanings) > 1:
            meanings = ["%d. %s" % (n+1, meaning) for n, meaning in enumerate(meanings)]

        cursor.execute("""INSERT into words (
            article_id, word, mark, definition)
            values (?, ?, ?, ?)""", (num_article, main_word_txt, mrk, '\n\n'.join(meanings)))
        row_id = cursor.lastrowid
        trads = extract_translations(drv, mrk)
        insert_translations(row_id, trads, cursor)

    return {'id': row_id, 'words': found_words}


def parse_snc(snc, drv, verbose=False):
    mrk = snc.get('mrk') or drv.get('mrk')
    radix = mrk.split('.')[0]
    # TODO markup! Example word: abdiki, adekva.0a.KOMUNE
    dif = snc.find('dif')
    if dif is None:
        dif = snc.find('./refgrp[@tip="dif"]')
        if dif is None:
            dif = snc.find('./ref[@tip="dif"]')
            # TODO read ekz tags, example: afekci.0i.MED
    dif_text = stringify_children(dif, radix, ignore=['trd'])

    subsncs = snc.findall('subsnc')
    subsncs = ["%s) %s" % (chr(ord('a')+n), parse_snc(subsnc, drv, verbose)[0])
               for n, subsnc in enumerate(subsncs)]
    if subsncs:
        dif_text += '\n\n'
        dif_text += '\n\n'.join(subsncs)

    uzo = snc.find('uzo')
    if uzo is not None:
        dif_text = uzo.text + " " + dif_text
    if verbose:
        print(mrk, uzo, dif_text)
    else:
        print(mrk)

    trads = extract_translations(snc, mrk)
    return (dif_text, trads)


@click.command()
@click.option('--word')
@click.option('--limit', type=int)
@click.option('--verbose', is_flag=True)
def main(word, limit, verbose):
    conn = create_db()
    cursor = conn.cursor()

    try:
        files = glob.glob('./xml/*.xml')
        files.sort()
        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            parse_article(filename, num_article, cursor, verbose)
            num_article += 1

            if limit and num_article >= limit:
                break
    finally:
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
