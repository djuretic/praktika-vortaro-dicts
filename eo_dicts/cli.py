import fire
from . import process_revo
from .utils import list_languages
from .search import search_multiple, stats
from typing import Optional


class Vortaro(object):
    def show_languages(self):
        list_languages()

    def search(self, *words: str):
        search_multiple(*words)

    def stats(self):
        stats()

    def process_revo(
        self,
        word: Optional[str] = None,
        xml_file: Optional[str] = None,
        output_db: str = "vortaro.db",
        limit: Optional[int] = None,
        verbose: bool = False,
        dry_run: bool = False,
        min_entries_to_include_lang: int = 100,
    ):
        process_revo.main(
            word,
            xml_file,
            output_db,
            limit,
            verbose,
            dry_run,
            min_entries_to_include_lang,
        )


def main():
    fire.Fire(Vortaro)


if __name__ == "__main__":
    main()
