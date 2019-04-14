import html2text
import os
from eo_dicts.parser.dictionary import DictionaryParser

def main():
    output_db = os.path.join(os.path.dirname(__file__), '..', 'output', 'aulex.db')
    with open('eo-es.htm') as f:
        text = html2text.html2text(f.read()).replace('_', '')
        DictionaryParser.parse_string(text, source_lang="eo", target_lang="es", output_db=output_db, output_table="aulex", header_lines=15)

    output_db = os.path.join(os.path.dirname(__file__), '..', 'output', 'aulex2.db')
    with open('es-eo.htm') as f:
        text = html2text.html2text(f.read()).replace('_', '')
        DictionaryParser.parse_string(text, source_lang="es", target_lang="eo", output_db=output_db, output_table="aulex", header_lines=15)

if __name__ == '__main__':
    main()
