import fire
from eo_dicts import process_revo
from eo_dicts.utils import list_languages


class Vortaro(object):
    def show_languages(self):
        list_languages()

    def process_revo(
        self,
        word: str = None,
        xml_file: str = None,
        output_db: str = "vortaro.db",
        limit: int = None,
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


if __name__ == "__main__":
    fire.Fire(Vortaro)
