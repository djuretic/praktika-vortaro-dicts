import click
import xml.etree.ElementTree as ET
from lxml import etree

EXTRA_TAGS = ['uzo', 'dif', 'trd', 'trdgrp']


def remove_extra_whitespace(string):
    string = string.replace("\n", "")
    cleaned = ' '.join(string.split())
    # Preserve trailing whitespace
    if string and string[-1] == ' ':
        cleaned += ' '
    return cleaned

class Node:
    tags = []
    def __init__(self, node, extra_info=None):
        self.parse_tags(node, extra_info)

    def __repr__(self):
        keys = ' '.join("{}={}".format(k, repr(v)) for k, v in self.__dict__.items())
        return "<%s %s>" % (self.__class__.__name__, keys)

    def parse_tags(self, node, extra_info):
        for tag in self.tags:
            tag_class = globals()[tag.title()]
            nodes = [tag_class(subnode, extra_info) for subnode in node.findall(tag)]
            if nodes:
                setattr(self, tag, nodes)
            else:
                setattr(self, tag, [])

    def parse_children(self, node, extra_info=None):
        self.text = []
        if node.text.strip():
            self.text.append(remove_extra_whitespace(node.text))
        for child in node:
            # TODO check ind in gust.xml
            if child.tag in ['fnt', 'ind']:
                continue
            tag_class = globals()[child.tag.title()]
            self.text.append(tag_class(child, extra_info))
            if child.tail.strip():
                self.text.append(remove_extra_whitespace(child.tail))

    def to_text(self):
        pass


class Art(Node):
    tags = ['subart', 'drv', 'snc'] + EXTRA_TAGS
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        assert node.tag == 'art'
        rad = node.find('kap/rad')
        self.kap = (rad.text, rad.tail.strip())

    def to_text(self):
        drv = [d.to_text() for d in self.drv]
        res = ''.join(drv)
        return res


class Subart(Node):
    tags = ['drv', 'snc'] + EXTRA_TAGS

    def __init__(self, node, extra_info=None):
        self.parse_tags(node)


class Drv(Node):
    tags = ['subdrv', 'snc'] + EXTRA_TAGS

    def __init__(self, node, extra_info=None):
        self.mrk = node.get('mrk')
        if not extra_info:
            extra_info = {}
        extra_info['radix'] = self.mrk.split('.')[0]
        super().__init__(node, extra_info)
        kap = node.find('kap/tld')
        self.kap = kap.tail

    def to_text(self):
        # TODO subdrv
        meanings = []
        for n, snc in enumerate(self.snc):
            text = snc.to_text()
            if len(self.snc) > 1:
                text = "%s. %s" % (n+1, text)
            meanings.append(text)
        print(meanings)
        return '\n\n'.join(meanings)


class Subdrv(Node):
    tags = ['snc']

    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)

class Snc(Node):
    tags = ['subsnc']  + EXTRA_TAGS

    def __init__(self, node, extra_info=None):
        self.mrk = node.get('mrk')
        if not extra_info:
            extra_info = {}
        # example: snc without mrk but drv has it (see zoni in zon.xml)
        mrk = self.mrk or extra_info['radix']
        extra_info['radix'] = mrk.split('.')[0]
        super().__init__(node, extra_info)

    def to_text(self):
        content = ''
        if self.uzo:
            content += ' '.join([u.to_text() for u in self.uzo]) + ' '
        content += '\n'.join([d.to_text() for d in self.dif])

        if self.subsnc:
            content += '\n\n'
            subs = []
            for n, subsnc in enumerate(self.subsnc):
                text = subsnc.to_text()
                subs.append("%s) %s" % (chr(ord('a')+n), text))
            content += '\n\n'.join(subs)

        return content

class Subsnc(Node):
    tags = EXTRA_TAGS

    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.mrk = node.get('mrk')

    def to_text(self):
        # TODO refactor (copied from Snc)
        content = ''
        if self.uzo:
            content += ' '.join([u.to_text() for u in self.uzo]) + ' '
        content += '\n'.join([d.to_text() for d in self.dif])
        return content


class Uzo(Node):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        # TODO tld tag
        self.text = node.text

    def to_text(self):
        return self.text


# TODO parse ekz tags
class Dif(Node):
    tags = ['trd']

    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.parse_children(node, extra_info)

    def to_text(self):
        parts = []
        for node in self.text:
            if isinstance(node, str):
                parts.append(node)
            else:
                parts.append(node.to_text())
        return ''.join(parts).strip()


class Trd(Node):
    def __init__(self, node, extra_info=None):
        self.text = node.text
        self.lng = node.get('lng')


class Trdgrp(Node):
    tags = ['trd']

    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.lng = node.get('lng')


class Ref(Node):
    def __init__(self, node, extra_info=None):
        self.text = node.text
        self.cel = node.get('cel')

    def to_text(self):
        # TODO include cel
        return self.text


class Ekz(Node):
    def __init__(self, node, extra_info=None):
        self.parse_children(node)


class Tld(Node):
    def __init__(self, node, extra_info=None):
        self.radix = None
        if extra_info:
            self.radix = extra_info['radix']

    def to_text(self):
        return self.radix or '-----'

# found in amik.xml
class Klr(Node):
    def __init__(self, node, extra_info=None):
        self.parse_children(node)

# found in zon.xml
class Frm(Node):
    def __init__(self, node, extra_info=None):
        self.text = node.text

    def to_text(self):
        return self.text

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


def parse_article(filename):
    with open(filename) as f:
        article = f.read()

    xml_parser = ET.XMLParser()
    for entity, value in entities_dict().items():
        xml_parser.entity[entity] = value
    tree = ET.fromstring(article, parser=xml_parser)

    art = tree.find('art')
    return Art(art)


@click.command()
@click.argument('word')
def main(word):
    art = parse_article('xml/%s.xml' % word)
    print(art)
    print()
    print(art.to_text())

if __name__ == '__main__':
    main()
