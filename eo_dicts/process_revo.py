import re
import os
import sqlite3
import glob
import itertools
from lxml import etree
import click

from .utils import add_hats, list_languages, get_languages
from .parser import revo


def insert_translations(trads, cursor):
    # flatten
    all_trans = []
    for translation in trads:
        for word in translation['data']:
            all_trans.append(dict(translation=word, **translation))

    all_trans.sort(key=lambda x: (x['lng'], x['translation']))

    for translation in all_trans:
        cursor.execute(
            """INSERT INTO translations_{code}
            (word_id, word, translation)
            VALUES (?,?,?)""".format(code=translation['lng']),
            (translation['row_id'], translation['word'], translation['translation'])
        )


def create_db(output_db):
    base_dir = os.path.dirname(__file__)
    db_filename = os.path.join(base_dir, output_db)
    try:
        os.remove(db_filename)
    except:
        pass
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    # position: relative order inside the article
    c.execute("""
        CREATE TABLE words (
            id integer primary key,
            article_id integer,
            word text,
            mark text,
            position integer,
            definition text,
            format text
        )
    """)

    return conn

def create_langs_tables(cursor, langs):
    cursor.execute("""
        CREATE TABLE languages (
            id integer primary key,
            code text,
            name text
        )
    """)

    lang_names = {
        lang_def['code']: (order, lang_def['name'])
        for order, lang_def in enumerate(get_languages())}
    # Normal sort won't consider ĉ, ŝ, ...,
    # get_languages() gives the correct order
    langs = sorted(langs, key=lambda x: lang_names[x][0])

    for lang in langs:
        cursor.execute("""
        CREATE TABLE translations_{lang} (
            id integer primary key,
            word_id integer,
            word text,
            translation text
        )
        """.format(lang=lang))

        cursor.execute("""
            INSERT INTO languages (code, name)
            VALUES (?, ?)
        """, (lang, lang_names[lang][1]))


def parse_article(filename, num_article, cursor, verbose=False):
    art = None
    try:
        art = revo.parse_article(filename)
    except:
        print('Error parsing %s' % filename)
        raise

    found_words = []
    entries = []
    has_subart = False
    drvs = list(art.derivations())
    for pos, drv in enumerate(drvs, 1):
        if isinstance(drv, revo.Subart):
            has_subart = True

        if pos == len(drvs) and has_subart and not drv.kap:
            # first subart contains the whole article,
            # so this snc will not be needed
            continue

        main_word_txt = drv.main_word()
        found_words.append(main_word_txt)
        row_id = None
        content = drv.to_text()
        assert 'StringWithFormat' not in content.string
        entries.append(
            dict(article_id=num_article, word=main_word_txt, mark=drv.mrk,
            definition=content.string, format=content.encode_format(),
            trads=drv.translations(), position=pos))

        if verbose:
            print(filename, drv.mrk, row_id)
        else:
            print(filename, drv.mrk)

    return entries


def create_index(cursor):
    cursor.execute("CREATE INDEX index_word_words ON words (word)")
    # cursor.execute("CREATE INDEX index_translations ON translations (lng, translation)")


def insert_entries(entries, cursor):
    entries = sorted(entries, key=lambda x: x['word'].lower())
    translations = []
    for entry in entries:
        print(entry['word'])
        tokens = [entry[x] for x in ('article_id', 'position', 'word', 'mark', 'definition', 'format')]
        cursor.execute("""INSERT into words (
            article_id, position, word, mark, definition, format)
            values (?, ?, ?, ?, ?, ?)""", tokens)
        row_id = cursor.lastrowid

        trads = entry['trads']
        if trads:
            for word, more_trads in trads.items():
                for lng, trans_data in more_trads.items():
                    translations.append(dict(row_id=row_id, word=word, lng=lng, data=trans_data))

    translations = sorted(translations, key= lambda x: x['lng'])
    shown_langs = []
    for lng, g in itertools.groupby(translations, key=lambda x: x['lng']):
        count = len(list(g))
        if count >= 100:
            print(lng, count)
            shown_langs.append(lng)

    create_langs_tables(cursor, shown_langs)
    translations = [t for t in translations if t['lng'] in shown_langs]
    insert_translations(translations, cursor)



@click.command()
@click.option('--word')
@click.option('--xml-file')
@click.option('--output-db', default='vortaro.db')
@click.option('--limit', type=int)
@click.option('--verbose', is_flag=True)
@click.option('--dry-run', is_flag=True)
@click.option('--show-languages', is_flag=True)
def main(word, xml_file, output_db, limit, verbose, dry_run, show_languages):
    if show_languages:
        list_languages()
        return

    conn = create_db(output_db)
    cursor = conn.cursor()

    entries = []
    try:
        files = []
        if xml_file:
            files = [xml_file]
        else:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, '..', 'revo', 'xml', '*.xml')
            files = glob.glob(path)
        files.sort()

        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            parsed_entries = parse_article(
                filename, num_article, cursor, verbose)
            entries += parsed_entries
            num_article += 1

            if limit and num_article >= limit:
                break

        if not dry_run:
            insert_entries(entries, cursor)
            create_index(cursor)
    finally:
        if not dry_run:
            conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
