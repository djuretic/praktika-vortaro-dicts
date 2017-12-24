import click
import xml.etree.ElementTree as ET
from lxml import etree

EXTRA_TAGS = ['uzo', 'dif', 'trd', 'trdgrp']


class Node:
    tags = []
    def __init__(self, node):
        self.parse_tags(node)

    def __repr__(self):
        keys = ' '.join("{}={}".format(k, repr(v)) for k, v in self.__dict__.items())
        return "<%s %s>" % (self.__class__.__name__, keys)

    def parse_tags(self, node):
        for tag in self.tags:
            tag_class = globals()[tag.title()]
            nodes = [tag_class(subnode) for subnode in node.findall(tag)]
            if nodes:
                setattr(self, tag, nodes)

    def parse_children(self, node):
        self.text = [node.text]
        for child in node:
            # TODO check ind in gust.xml
            if child.tag in ['fnt', 'ind']:
                continue
            tag_class = globals()[child.tag.title()]
            self.text.append(tag_class(child))
            self.text.append(child.tail)

    def to_text(self):
        # TODO
        pass


class Art(Node):
    tags = ['subart', 'drv', 'snc'] + EXTRA_TAGS
    def __init__(self, node):
        super().__init__(node)
        assert node.tag == 'art'
        rad = node.find('kap/rad')
        self.kap = (rad.text, rad.tail.strip())


class Subart(Node):
    tags = ['drv', 'snc'] + EXTRA_TAGS

    def __init__(self, node):
        self.parse_tags(node)


class Drv(Node):
    tags = ['subdrv', 'snc'] + EXTRA_TAGS

    def __init__(self, node):
        super().__init__(node)
        self.mrk = node.get('mrk')
        kap = node.find('kap/tld')
        self.kap = kap.tail


class Subdrv(Node):
    tags = ['snc']

    def __init__(self, node):
        super().__init__(node)

class Snc(Node):
    tags = ['subsnc']  + EXTRA_TAGS

    def __init__(self, node):
        super().__init__(node)
        self.mrk = node.get('mrk')


class Subsnc(Node):
    tags = EXTRA_TAGS

    def __init__(self, node):
        super().__init__(node)
        self.mrk = node.get('mrk')


class Uzo(Node):
    def __init__(self, node):
        super().__init__(node)
        # TODO tld tag
        self.text = node.text


class Dif(Node):
    tags = ['trd']

    def __init__(self, node):
        super().__init__(node)
        # TODO stringify
        self.parse_children(node)


class Trd(Node):
    def __init__(self, node):
        self.text = node.text
        self.lng = node.get('lng')


class Trdgrp(Node):
    tags = ['trd']

    def __init__(self, node):
        super().__init__(node)
        self.lng = node.get('lng')


class Ref(Node):
    def __init__(self, node):
        self.text = node.text
        self.cel = node.get('cel')


class Ekz(Node):
    def __init__(self, node):
        self.parse_children(node)


class Tld(Node):
    pass

# found in amik.xml
class Klr(Node):
    def __init__(self, node):
        self.parse_children(node)

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
    print(art.to_text())

if __name__ == '__main__':
    main()
