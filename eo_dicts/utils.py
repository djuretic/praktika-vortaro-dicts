import xml.etree.ElementTree as ET
import os

MAPPING = {
    'C': 'Ĉ',
    'G': 'Ĝ',
    'H': 'Ĥ',
    'J': 'Ĵ',
    'S': 'Ŝ',
    'U': 'Ŭ',
    'c': 'ĉ',
    'g': 'ĝ',
    'h': 'ĥ',
    'j': 'ĵ',
    's': 'ŝ',
    'u': 'ŭ',
}


def add_hats(word):
    if not word or len(word) == 1:
        return word
    res = ''
    pos = 0
    while pos < len(word) - 1:
        char = word[pos]
        if char in MAPPING.keys() and word[pos+1] in ('x', 'X'):
            res += MAPPING[char]
            pos += 2
        else:
            res += char
            pos += 1
    if pos == len(word) - 1:
        res += word[-1]
    return res

def get_languages():
    base_dir = os.path.dirname(__file__)
    xml_path = os.path.join(base_dir, '..', 'revo', 'cfg', 'lingvoj.xml')
    tree = ET.parse(xml_path)
    langs = tree.findall('lingvo')
    alphabet = 'abcĉdefgĝhĥijĵklmnoprsŝtuŭvz/-'
    # normal sort puts ĉ, ĝ,... at the end
    langs = sorted(langs, key=lambda x: [alphabet.index(c) for c in x.text])
    return [{'code': lang.get('kodo'), 'name': lang.text } for lang in langs]

def get_disciplines():
    base_dir = os.path.dirname(__file__)
    xml_path = os.path.join(base_dir, '..', 'revo', 'cfg', 'fakoj.xml')
    tree = ET.parse(xml_path)
    return {node.get('kodo'): node.text for node in tree.findall('fako')}

def list_languages():
    langs = get_languages()
    for n, lang in enumerate(langs, 1):
        print(n, lang['code'], lang['name'])

def letter_enumerate(iterable):
    for n, elem in enumerate(iterable):
        yield (chr(ord('a')+n), elem)

def output_dir():
    return os.path.join(os.path.dirname(__file__), "..", "output")
