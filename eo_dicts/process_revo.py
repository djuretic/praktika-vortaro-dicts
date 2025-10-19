import os
import sqlite3
import glob
import itertools
import json
from typing import TypedDict, Optional

from .utils import get_languages, get_disciplines, output_dir
from .parser import revo
from .parser.string_with_format import expand_tld


class DefinitionDict(TypedDict):
    article_id: int
    word: str
    mark: str
    definition: str
    format: str
    trads: dict
    position: int
    definition_id: Optional[int]


class EntryDict(TypedDict):
    article_id: int
    word: str
    definition: DefinitionDict


def insert_translations(trads: list[dict], cursor: sqlite3.Cursor) -> None:
    # flatten
    all_trans: list[dict] = []
    for translation in trads:
        for snc_index, words in translation["data"].items():
            for word in words:
                all_trans.append(
                    dict(translation=word, snc_index=snc_index, **translation)
                )

    all_trans.sort(
        key=lambda x: (
            x["lng"],
            x["translation"],
            x["snc_index"] is None,
            x["snc_index"],
        )
    )

    for translation in all_trans:
        cursor.execute(
            """INSERT INTO translations_{code}
            (definition_id, snc_index, word, translation)
            VALUES (?,?,?,?)""".format(code=translation["lng"]),
            (
                translation["row_id"],
                translation["snc_index"],
                translation["word"],
                translation["translation"],
            ),
        )


def create_db(output_db: str) -> sqlite3.Connection:
    base_dir = os.path.dirname(__file__)
    db_filename = os.path.join(base_dir, output_db)
    try:
        os.remove(db_filename)
    except Exception:
        pass
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE words (
            id integer primary key,
            word text,
            definition_id integer
        )
    """
    )
    # position: relative order inside the article
    c.execute(
        """
        CREATE TABLE definitions (
            id integer primary key,
            article_id integer,
            words text,
            mark text,
            position integer,
            definition text,
            format text
        )
    """
    )

    return conn


def create_langs_tables(cursor: sqlite3.Cursor, entries_per_lang: dict) -> None:
    cursor.execute(
        """
        CREATE TABLE languages (
            id integer primary key,
            code text,
            name text,
            num_entries integer
        )
    """
    )

    lang_names = {
        lang_def["code"]: (order, lang_def["name"])
        for order, lang_def in enumerate(get_languages())
    }
    # Normal sort won't consider ĉ, ŝ, ...,
    # get_languages() gives the correct order
    # Some language codes may appear in entries_per_lang but not in the
    # lingvoj.xml file (e.g. uncommon or unexpected codes). In that case
    # fall back to using the code itself as name and a large order so they
    # appear at the end. Also print a warning to help detect missing codes.
    def lang_order(code: str) -> int:
        info = lang_names.get(code)
        if info is None:
            print(f"Warning: language code '{code}' not found in lingvoj.xml; using fallback order and name")
            return 10 ** 6
        return info[0]

    langs = sorted(entries_per_lang.keys(), key=lang_order)

    for lang in langs:
        cursor.execute(
            """
        CREATE TABLE translations_{lang} (
            id integer primary key,
            definition_id integer,
            snc_index integer,
            word text,
            translation text
        )
        """.format(lang=lang)
        )

        # Use the provided name if available; otherwise fall back to the
        # language code itself so the DB still contains a readable value.
        name = lang_names.get(lang, (None, lang))[1]
        cursor.execute(
            """
            INSERT INTO languages (code, name, num_entries)
            VALUES (?, ?, ?)
        """,
            (lang, name, entries_per_lang[lang]),
        )


def create_disciplines_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE disciplines (
            id integer primary key,
            code text,
            name text
        )
    """
    )

    for code, discipline in get_disciplines().items():
        cursor.execute(
            "INSERT INTO disciplines (code, name) VALUES (?, ?)", (code, discipline)
        )


def create_version_table(cursor: sqlite3.Cursor) -> None:
    base_dir = os.path.dirname(__file__)
    version = ""
    with open(os.path.join(base_dir, "..", "revo", "VERSION"), "r") as f:
        version = f.read().strip()

    cursor.execute("CREATE TABLE version (id text primary key)")
    cursor.execute("INSERT INTO version (id) values (?)", (version,))


def parse_article(filename: str, num_article: int, verbose=False) -> list[EntryDict]:
    art = None
    try:
        art = revo.parse_article(filename)
    except Exception:
        print("Error parsing %s" % filename)
        raise

    found_words = []
    entries: list[EntryDict] = []
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
        content = expand_tld(content)
        assert "StringWithFormat" not in content.string

        # definition_id will be used to check whether the definition is already in the database
        definition: DefinitionDict = dict(
            article_id=num_article,
            word=main_word_txt,
            mark=drv.mrk,
            definition=content.string,
            format=content.encode_format(),
            trads=drv.translations(),
            position=pos,
            definition_id=None,
        )
        # note that before inserting the entries will be sorted by 'word'
        first_word = True
        for word in main_word_txt.split(", "):
            word = word.strip()
            # "definition" dict is shared between entries in this loop
            entries.append(
                dict(article_id=num_article, word=word, definition=definition)
            )
            if first_word:
                first_word = False
                # Avoid duplication of translations
                definition = definition.copy()
                definition["trads"] = {}

        if verbose:
            print(filename, drv.mrk, row_id)
        else:
            print(filename, drv.mrk)

    return entries


def create_index(cursor: sqlite3.Cursor) -> None:
    cursor.execute("CREATE INDEX index_word_words ON words (word)")
    cursor.execute("CREATE INDEX index_definition_id_words ON words (definition_id)")


def write_stats(entries_per_lang: dict) -> None:
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(base_dir, "..", "stats.json"), "w") as f:
        json.dump(entries_per_lang, f, ensure_ascii=False, indent=4)


def insert_entries(
    entries: list[EntryDict], cursor: sqlite3.Cursor, min_entries_to_include_lang: int
) -> None:
    entries = sorted(entries, key=lambda x: x["word"].lower())
    translations = []
    for entry in entries:
        print(entry["word"])

        if not entry["definition"]["definition_id"]:
            definition = entry["definition"]
            cursor.execute(
                """INSERT INTO definitions (
                article_id, words, mark, position, definition, format)
                values (?, ?, ?, ?, ?, ?)""",
                (
                    definition["article_id"],
                    definition["word"],
                    definition["mark"],
                    definition["position"],
                    definition["definition"],
                    definition["format"],
                ),
            )
            entry["definition"]["definition_id"] = cursor.lastrowid

        assert entry["definition"]["definition_id"] is not None
        def_id: int = entry["definition"]["definition_id"]

        cursor.execute(
            "INSERT into words (word, definition_id) values (?, ?)",
            [entry["word"], def_id],
        )

        trads = entry["definition"]["trads"]
        if trads:
            for word, more_trads in trads.items():
                for lng, trans_data in more_trads.items():
                    translations.append(
                        dict(row_id=def_id, word=word, lng=lng, data=trans_data)
                    )

    translations = sorted(translations, key=lambda x: x["lng"])
    entries_per_lang = {}
    for lng, g in itertools.groupby(translations, key=lambda x: x["lng"]):
        count = len(list(g))
        if count >= min_entries_to_include_lang:
            print(lng, count)
            entries_per_lang[lng] = count

    write_stats(entries_per_lang)

    create_langs_tables(cursor, entries_per_lang)
    translations = [t for t in translations if t["lng"] in entries_per_lang]
    insert_translations(translations, cursor)


def main(
    word: Optional[str],
    xml_file: Optional[str],
    output_db: str,
    limit: Optional[int],
    verbose: bool,
    dry_run: bool,
    min_entries_to_include_lang: int,
) -> None:
    conn = create_db(os.path.join(output_dir(), output_db))
    cursor = conn.cursor()

    if not dry_run:
        create_disciplines_tables(cursor)

    entries: list[EntryDict] = []
    try:
        files = []
        if xml_file:
            files = [xml_file]
        else:
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, "..", "revo", "xml", "*.xml")
            files = glob.glob(path)
        files.sort()

        num_article = 1
        for filename in files:
            if word and word not in filename:
                continue
            parsed_entries = parse_article(filename, num_article, verbose)
            entries += parsed_entries
            num_article += 1

            if limit and num_article >= limit:
                break

        if not dry_run:
            insert_entries(entries, cursor, min_entries_to_include_lang)
            create_index(cursor)
            create_version_table(cursor)
    finally:
        if not dry_run:
            conn.commit()
        cursor.close()
        conn.close()
