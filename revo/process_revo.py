import re
import sqlite3
import glob
from lxml import etree
import click

from utils import add_hats, list_languages
import parser.revo


def insert_translations(word_id, trads, cursor):
    if not trads:
        return
    for word, more_trads in trads.items():
        for lng, translations in more_trads.items():
            for translation in translations:
                cursor.execute(
                    "INSERT INTO translations (word_id, word, lng, translation) VALUES (?,?,?,?)",
                    (word_id, word, lng, translation)
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
            definition text,
            format text
        )
    """)

    c.execute('DROP TABLE if exists translations')
    c.execute("""
        CREATE TABLE translations (
            id integer primary key,
            word_id integer,
            word text,
            lng text,
            translation text
        )
    """)
    c.close()
    return conn

def parse_article(filename, num_article, cursor, verbose=False, dry_run=False):
    art = None
    try:
        art = parser.revo.parse_article(filename)
    except:
        print('Error parsing %s' % filename)
        raise

    found_words = []
    for drv in art.derivations():
        main_word_txt = drv.main_word()
        found_words.append(main_word_txt)
        row_id = None
        if not dry_run:
            content = drv.to_text()
            assert 'StringWithFormat' not in content.string
            tokens = (num_article, main_word_txt, drv.mrk, content.string, content.encode_format())
            cursor.execute("""INSERT into words (
                article_id, word, mark, definition, format)
                values (?, ?, ?, ?, ?)""", tokens)
            row_id = cursor.lastrowid

            trads = drv.translations()
            if trads:
                insert_translations(row_id, trads, cursor)

        if verbose:
            print(filename, drv.mrk, row_id)
        else:
            print(filename, drv.mrk)

    return {'id': row_id, 'words': found_words}


def create_index(cursor):
    cursor.execute("CREATE INDEX index_word_words ON words (word)")
    cursor.execute("CREATE INDEX index_translations ON translations (lng, translation)")


@click.command()
@click.option('--word')
@click.option('--limit', type=int)
@click.option('--verbose', is_flag=True)
@click.option('--dry-run', is_flag=True)
@click.option('--show-languages', is_flag=True)
def main(word, limit, verbose, dry_run, show_languages):
    if show_languages:
        list_languages()
        return

    conn = create_db()
    cursor = conn.cursor()

    try:
        files = glob.glob('./xml/*.xml')
        files.sort()
        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            parse_article(filename, num_article, cursor, verbose, dry_run)
            num_article += 1

            if limit and num_article >= limit:
                break
        create_index(cursor)
    finally:
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
