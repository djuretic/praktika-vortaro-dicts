import xml.etree.ElementTree as ET

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

def list_languages():
    tree = ET.parse("./cfg/lingvoj.xml")
    langs = tree.findall('lingvo')
    alphabet = 'abcĉdefgĝhĥijĵklmnoprsŝtuŭvz/-'
    # normal sort puts ĉ, ĝ,... at the end
    langs = sorted(langs, key=lambda x: [alphabet.index(c) for c in x.text])
    for n, lang in enumerate(langs, 1):
        print(n, lang.get('kodo'), lang.text)
