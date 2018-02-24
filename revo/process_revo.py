import re
import os
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
    db_filename = 'vortaro.db'
    os.remove(db_filename)
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
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
    entries = []
    for drv in art.derivations():
        main_word_txt = drv.main_word()
        found_words.append(main_word_txt)
        row_id = None
        if not dry_run:
            content = drv.to_text()
            assert 'StringWithFormat' not in content.string
            entries.append(
                dict(article_id=num_article, word=main_word_txt, mark=drv.mrk,
                definition=content.string, format=content.encode_format(),
                trads=drv.translations()))

        if verbose:
            print(filename, drv.mrk, row_id)
        else:
            print(filename, drv.mrk)

    return entries


def create_index(cursor):
    cursor.execute("CREATE INDEX index_word_words ON words (word)")
    cursor.execute("CREATE INDEX index_translations ON translations (lng, translation)")


def insert_entries(entries, cursor):
    entries = sorted(entries, key=lambda x: x['word'].lower())
    for entry in entries:
        print(entry['word'])
        tokens = [entry[x] for x in ('article_id', 'word', 'mark', 'definition', 'format')]
        cursor.execute("""INSERT into words (
            article_id, word, mark, definition, format)
            values (?, ?, ?, ?, ?)""", tokens)
        row_id = cursor.lastrowid

        trads = entry['trads']
        if trads:
            insert_translations(row_id, trads, cursor)


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

    entries = []
    try:
        files = glob.glob('./xml/*.xml')
        files.sort()
        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            parsed_entries = parse_article(
                filename, num_article, cursor, verbose, dry_run)
            entries += parsed_entries
            num_article += 1

            if limit and num_article >= limit:
                break

        insert_entries(entries, cursor)
        create_index(cursor)
    finally:
        conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
