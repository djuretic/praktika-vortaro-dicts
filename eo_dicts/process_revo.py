import re
import os
import sqlite3
import glob
import itertools
from lxml import etree
import click

from .utils import add_hats, list_languages, get_languages, get_disciplines
from .parser import revo


def insert_translations(trads, cursor):
    # flatten
    all_trans = []
    for translation in trads:
        for snc_index, words in translation['data'].items():
            for word in words:
                all_trans.append(dict(translation=word, snc_index=snc_index, **translation))

    all_trans.sort(key=lambda x: (x['lng'], x['translation'], x['snc_index'] is None, x['snc_index']))

    for translation in all_trans:
        cursor.execute(
            """INSERT INTO translations_{code}
            (definition_id, snc_index, word, translation)
            VALUES (?,?,?,?)""".format(code=translation['lng']),
            (translation['row_id'], translation['snc_index'], translation['word'], translation['translation'])
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
    c.execute("""
        CREATE TABLE words (
            id integer primary key,
            word text,
            definition_id integer
        )
    """)
    # position: relative order inside the article
    c.execute("""
        CREATE TABLE definitions (
            id integer primary key,
            article_id integer,
            words text,
            mark text,
            position integer,
            definition text,
            format text
        )
    """)

    return conn

def create_langs_tables(cursor, entries_per_lang):
    cursor.execute("""
        CREATE TABLE languages (
            id integer primary key,
            code text,
            name text,
            num_entries integer
        )
    """)

    lang_names = {
        lang_def['code']: (order, lang_def['name'])
        for order, lang_def in enumerate(get_languages())}
    # Normal sort won't consider ĉ, ŝ, ...,
    # get_languages() gives the correct order
    langs = sorted(entries_per_lang.keys(), key=lambda x: lang_names[x][0])

    for lang in langs:
        cursor.execute("""
        CREATE TABLE translations_{lang} (
            id integer primary key,
            definition_id integer,
            snc_index integer,
            word text,
            translation text
        )
        """.format(lang=lang))

        cursor.execute("""
            INSERT INTO languages (code, name, num_entries)
            VALUES (?, ?, ?)
        """, (lang, lang_names[lang][1], entries_per_lang[lang]))

def create_disciplines_tables(cursor):
    cursor.execute("""
        CREATE TABLE disciplines (
            id integer primary key,
            code text,
            name text
        )
    """)

    for code, discipline in get_disciplines().items():
        cursor.execute(
            "INSERT INTO disciplines (code, name) VALUES (?, ?)",
            (code, discipline))


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

        # definition_id will be used to check whether the definition is already in the database
        definition = dict(article_id=num_article, word=main_word_txt, mark=drv.mrk,
            definition=content.string, format=content.encode_format(),
            trads=drv.translations(), position=pos, definition_id=None)
        # note that before inserting the entries will be sorted by 'word'
        for word in main_word_txt.split(', '):
            word = word.strip()
            # "definition" dict is shared between entries in this loop
            entries.append(
                dict(article_id=num_article, word=word, definition=definition))

        if verbose:
            print(filename, drv.mrk, row_id)
        else:
            print(filename, drv.mrk)

    return entries


def create_index(cursor):
    cursor.execute("CREATE INDEX index_word_words ON words (word)")
    cursor.execute("CREATE INDEX index_definition_id_words ON words (definition_id)")


def insert_entries(entries, cursor, min_entries_to_include_lang):
    entries = sorted(entries, key=lambda x: x['word'].lower())
    translations = []
    for entry in entries:
        print(entry['word'])

        if not entry['definition']['definition_id']:
            definition = entry['definition']
            cursor.execute("""INSERT INTO definitions (
                article_id, words, mark, position, definition, format)
                values (?, ?, ?, ?, ?, ?)""", (
                    definition['article_id'], definition['word'],
                    definition['mark'], definition['position'],
                    definition['definition'], definition['format']))
            entry['definition']['definition_id'] = cursor.lastrowid
        def_id = entry['definition']['definition_id']

        cursor.execute(
            "INSERT into words (word, definition_id) values (?, ?)",
            [entry['word'], def_id]
        )

        trads = entry['definition']['trads']
        if trads:
            for word, more_trads in trads.items():
                for lng, trans_data in more_trads.items():
                    translations.append(dict(row_id=def_id, word=word, lng=lng, data=trans_data))

    translations = sorted(translations, key= lambda x: x['lng'])
    entries_per_lang = {}
    for lng, g in itertools.groupby(translations, key=lambda x: x['lng']):
        count = len(list(g))
        if count >= min_entries_to_include_lang:
            print(lng, count)
            entries_per_lang[lng] = count

    create_langs_tables(cursor, entries_per_lang)
    translations = [t for t in translations if t['lng'] in entries_per_lang]
    insert_translations(translations, cursor)



@click.command()
@click.option('--word')
@click.option('--xml-file')
@click.option('--output-db', default='vortaro.db')
@click.option('--limit', type=int)
@click.option('--verbose', is_flag=True)
@click.option('--dry-run', is_flag=True)
@click.option('--show-languages', is_flag=True)
@click.option('--min-entries-to-include-lang', type=int, default=100)
def main(word, xml_file, output_db, limit, verbose, dry_run, show_languages, min_entries_to_include_lang):
    if show_languages:
        list_languages()
        return

    conn = create_db(output_db)
    cursor = conn.cursor()

    if not dry_run:
        create_disciplines_tables(cursor)

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
            insert_entries(entries, cursor, min_entries_to_include_lang)
            create_index(cursor)
    finally:
        if not dry_run:
            conn.commit()
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
