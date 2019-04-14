import html2text
import os
from eo_dicts.parser.dictionary import DictionaryParser

def main():
    output_db = os.path.join(os.path.dirname(__file__), '..', 'output', 'aulex.db')
    with open('eo-es.htm') as f:
        text = html2text.html2text(f.read()).replace('_', '')
        DictionaryParser.parse_string(text, target_lang="es", output_db=output_db, output_table="aulex", header_lines=5)

if __name__ == '__main__':
    main()
