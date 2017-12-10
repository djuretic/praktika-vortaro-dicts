import sqlite3
import glob
import xml.etree.ElementTree as ET
from lxml import etree
import click

# https://stackoverflow.com/a/28173933
def stringify_children(node):
    if node is None:
        return ''
    s = node.text
    if s is None:
        s = ''
    for child in node:
        s += ET.tostring(child, encoding='unicode')
    return ' '.join(s.strip().replace("\n", "").split())


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
    c.execute('CREATE TABLE words (id integer primary key, base text, word text, definition text) ')
    c.close()
    return conn


def get_main_word(mrk):
    parts = mrk.split('.')
    return parts[1].replace('0', parts[0])


@click.command()
@click.option('--word')
@click.option('--verbose', is_flag=True)
def main(word, verbose):
    conn = create_db()
    c = conn.cursor()

    try:
        files = glob.glob('./xml/*.xml')
        files.sort()
        for filename in files:
            if word and word not in filename:
                continue
            article = None
            with open(filename) as f:
                article = f.read()

            with open('output.xml', 'w') as f:
                f.write(article)

            # print(article)
            xml_parser = ET.XMLParser()
            for entity, value in entities_dict().items():
                xml_parser.entity[entity] = value
            tree = ET.fromstring(article, parser=xml_parser)

            for art in tree.findall('art'):
                main_word = art.find('kap/rad')
                # main_word_txt = (main_word.text + main_word.tail).replace("/", "")
                if verbose:
                    print(main_word)

                for drv in art.findall('drv'):
                    # Example: afekcii has <dif> here
                    meanings = []
                    dif = drv.find('dif')
                    if dif is not None:
                        meanings.append(stringify_children(dif))
                    # TODO initial
                    # word = drv.find('kap')
                    # print(word.find('tld').tail)

                    # TODO drv also has dif

                    for snc in drv.findall('snc'):
                        mrk = snc.get('mrk') or drv.get('mrk')
                        use = snc.find('uzo')
                        if use:
                            use = use.text
                        # TODO markup! Example word: abdiki, adekva.0a.KOMUNE
                        dif = snc.find('dif')
                        if dif is None:
                            dif = snc.find('./refgrp[@tip="dif"]')
                            if dif is None:
                                dif = snc.find('./ref[@tip="dif"]')
                                # TODO read ekz tags, example: afekci.0i.MED
                        dif_text = stringify_children(dif)
                        # TODO numbering, anchor to mrk name
                        meanings.append(dif_text)
                        if verbose:
                            print(mrk, use, dif_text)
                        else:
                            print(mrk)

                        # print(snc.get('mrk'), ''.join(dif.itertext()))

                        extract_translations(snc)

                    mrk = drv.get('mrk')
                    # TODO uppercase if it's a name
                    main_word_txt = get_main_word(mrk)
                    c.execute('INSERT into words (base, word, definition) values (?, ?, ?)', (main_word_txt, mrk, '\n---\n'.join(meanings)))
                    extract_translations(drv)
    finally:
        conn.commit()
        c.close()
        conn.close()


if __name__ == '__main__':
    main()
