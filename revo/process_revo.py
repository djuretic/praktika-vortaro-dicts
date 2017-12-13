import re
import sqlite3
import glob
import xml.etree.ElementTree as ET
from lxml import etree
import click
from pygtrie import CharTrie

from utils import add_hats


def stringify_children(node, word=None, first=True):
    # print(node, "Word: ", word)
    if node is None:
        return ''
    s = node.text
    if s is None:
        s = ''
    if node.tag in ['adm', 'bld', 'fnt']:
        # Ignore them
        if node.tail:
            s += node.tail
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
        s += stringify_children(child, word, first=False)

    if not has_child and node.tail:
        s += node.tail

    # print(node, "Word: ", word, "Res:", s)
    if first:
        return ' '.join(s.strip().replace("\n", "").split())
    return s


def extract_translations(node):
    return
    for trd in node.findall('trd'):
        print(node.get('mrk'), trd.get('lng'), trd.text)
    for trdgrp in node.findall('trdgrp'):
        for trd in trdgrp.findall('trd'):
            print(node.get('mrk'), trdgrp.get('lng'), trd.text)


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
    c.execute("""CREATE TABLE words (
        id integer primary key,
        article_id integer,
        word text,
        mark text,
        definition text) """)
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
    # main_word_txt = (main_word.text + main_word.tail).replace("/", "")
    if verbose:
        print(main_word)

    row_id = None
    found_words = []
    for drv in art.findall('drv'):
        # Example: afekcii has <dif> here
        meanings = []
        dif = drv.find('dif')
        mrk = drv.get('mrk')
        # TODO uppercase if it's a name
        main_word_txt = get_main_word(mrk)
        found_words.append(main_word_txt)
        if dif is not None:
            meanings.append(stringify_children(dif))
        # TODO initial
        # word = drv.find('kap')
        # print(word.find('tld').tail)

        # TODO drv also has dif

        for snc in drv.findall('snc'):
            meanings.append(parse_snc(snc, drv, verbose))

        if len(meanings) > 1:
            meanings = ["%d. %s" % (n+1, meaning) for n, meaning in enumerate(meanings)]

        cursor.execute("""INSERT into words (
            article_id, word, mark, definition)
            values (?, ?, ?, ?)""", (num_article, main_word_txt, mrk, '\n\n'.join(meanings)))
        row_id = cursor.lastrowid
        extract_translations(drv)
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
    # TODO parse multiple uzo (a1.xml)
    dif_text = stringify_children(dif, radix)

    subsncs = snc.findall('subsnc')
    subsncs = ["%s) %s" % (chr(ord('a')+n), parse_snc(subsnc, drv, verbose))
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

    # print(snc.get('mrk'), ''.join(dif.itertext()))
    extract_translations(snc)
    return dif_text


@click.command()
@click.option('--word')
@click.option('--verbose', is_flag=True)
def main(word, verbose):
    conn = create_db()
    cursor = conn.cursor()
    trie = CharTrie()

    try:
        files = glob.glob('./xml/*.xml')
        files.sort()
        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            res = parse_article(filename, num_article, cursor, verbose)
            num_article += 1
            for found_word in res['words']:
                trie[found_word] = res['id']
    finally:
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
