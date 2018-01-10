import click
import xml.etree.ElementTree as ET
from lxml import etree
from .string_with_format import StringWithFormat, Format


def remove_extra_whitespace(string):
    cleaned = ' '.join(string.split())
    # Preserve trailing whitespace
    if string and string[-1] == ' ':
        cleaned += ' '
    return cleaned

class Node:
    def __init__(self, node, extra_info=None):
        if extra_info is None:
            extra_info = {}
        self.parse_children(node, extra_info)
        if extra_info:
            self.parent = extra_info.get('parent')

    def __repr__(self):
        keys = ' '.join("{}={}".format(k, repr(v)) for k, v in self.__dict__.items())
        return "<%s %s>" % (self.__class__.__name__, keys)

    def parse_children(self, node, extra_info=None):
        self.children = []
        if node.text and node.text.strip():
            self.children.append(remove_extra_whitespace(node.text))
        for child in node:
            if child.tag in ['adm', 'bld', 'fnt']:
                if child.tail and child.tail.strip():
                    self.children.append(remove_extra_whitespace(child.tail))
                continue
            tag_class = globals()[child.tag.title()]
            extra_info['parent'] = node
            self.children.append(tag_class(child, extra_info))
            if child.tail and child.tail.strip():
                if child.tag in ['ref', 'tld'] and child.tail[0] in [" ", "\n"]:
                    self.children.append(" ")
                self.children.append(remove_extra_whitespace(child.tail))

    def get(self, *args):
        "Get nodes based on their class"
        for tag in self.children:
            if tag.__class__ in args:
                yield tag

    def get_except(self, *args):
        for tag in self.children:
            if tag.__class__ not in args:
                yield tag

    def to_text(self):
        pass


class TextNode(Node):
    # Format enum
    base_format = None

    def to_text(self):
        parts = []
        for node in self.children:
            if isinstance(node, str):
                parts.append(StringWithFormat(node))
            else:
                parts.append(node.to_text())
        try:
            content = StringWithFormat()
            for part in parts:
                content += part
            return content.strip().apply_format(self.base_format)
        except:
            print(self.children)
            print(parts)
            raise


class Art(Node):
    def __init__(self, node, extra_info=None):
        if extra_info is None:
            extra_info = {}
        assert node.tag == 'art'
        rad = node.find('kap/rad')
        tail = ''
        if rad.tail:
            tail = rad.tail.strip()
        self.kap = (rad.text, tail)
        extra_info['radix'] = self.kap[0]
        super().__init__(node, extra_info)

    def derivations(self):
        for subart in self.get(Subart):
            for drv in subart.derivations():
                    yield drv
        for drv in self.get(Drv):
            yield drv
        assert not list(self.get(Snc))

    def to_text(self):
        raise Exception('Do not use Art.to_text() directly')


class Kap(TextNode):
    pass


class Rad(TextNode):
    pass


class Gra(TextNode):
    pass


class Mlg(TextNode):
    pass


class Vspec(TextNode):
    def to_text(self):
        return "(%s)" % super().to_text()

class Ofc(TextNode):
    def to_text(self):
        return ''


class Var(TextNode):
    pass


class Subart(TextNode):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.mrk = ''

    def derivations(self):
        for drv in self.get(Drv):
            yield drv
        # al.xml, last <subart>
        # TODO multiple snc, add numbering and line breaks
        if self.get(Snc):
            yield self

# TODO process variants (ex: elreviĝo, disreviĝo)
class Drv(Node):
    def __init__(self, node, extra_info=None):
        self.mrk = node.get('mrk')
        if not extra_info:
            extra_info = {}
        kap = Kap(node.find('kap'), extra_info)
        self.kap = kap.to_text().string
        super().__init__(node, extra_info)
        self.parse_children(node, extra_info)

    def to_text(self):
        meanings = []
        content = StringWithFormat()

        # Kap and Fnt ignored
        for node in self.get(Gra, Uzo, Dif, Ref):
            if isinstance(node, Ref) and node.tip != 'dif':
                continue
            content += node.to_text()

        n_sncs = len(list(self.get(Snc)))
        for n, snc in enumerate(self.get(Snc)):
            if n_sncs > 1:
                text = StringWithFormat("%s. " % (n+1,))
                text += snc.to_text()
            else:
                text = snc.to_text()
            meanings.append(text)

        for n, subdrv in enumerate(self.get(Subdrv)):
            text = subdrv.to_text()
            # if len(self.snc) > 1:
            #     text = "%s. %s" % (n+1, text)
            meanings.append(text)

        content += StringWithFormat.join(meanings, '\n\n')

        for node in self.get_except(Subdrv, Snc, Gra, Uzo, Fnt, Kap, Dif, Mlg):
            if isinstance(node, Ref) and node.tip == 'dif':
                continue
            content += node.to_text()

        # if self.rim:
        #     # multiple seen on akuzat.xml
        #     rim_txt = [rim.to_text() for rim in self.rim]
        #     content += "\n\n%s" % '\n\n'.join(rim_txt)
        # if self.ref:
        #     # multiple seen on amik.xml
        #     ref_txt = [ref.to_text() for ref in self.ref]
        #     content += "\n\n%s" % (' '.join(ref_txt))

        return content

class Subdrv(Node):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.parse_children(node, extra_info)

    def to_text(self):
        # TODO cycle letter
        letter = ord('A')
        content = StringWithFormat("\n\n%s. " % chr(letter))

        # Fnt omitted
        for node in self.get(Dif, Gra, Uzo, Ref):
            if isinstance(node, Ref) and ref.tip != 'dif':
                continue
            content += node.to_text()
        return content

class Snc(Node):
    def __init__(self, node, extra_info=None):
        self.mrk = node.get('mrk')
        if not extra_info:
            extra_info = {}
        # example: snc without mrk but drv has it (see zoni in zon.xml)
        mrk = self.mrk or extra_info['radix']
        super().__init__(node, extra_info)

    def to_text(self):
        content = StringWithFormat()

        # Fnt ignored
        for node in self.get(Gra, Uzo, Dif, Ref):
            if isinstance(node, Ref) and node.tip != 'dif':
                continue
            content += node.to_text()

        if list(self.get(Subsnc)):
            content += '\n\n'
            subs = []
            for n, subsnc in enumerate(self.get(Subsnc)):
                text = subsnc.to_text()
                text.prepend("%s) " % (chr(ord('a')+n),))
                subs.append(text)
            content += StringWithFormat.join(subs, '\n\n')

        for node in self.get_except(Gra, Uzo, Fnt, Dif, Subsnc):
            if isinstance(node, Ref) and node.tip == 'dif':
                continue
            content += node.to_text()

        return content

class Subsnc(TextNode):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.mrk = node.get('mrk')


class Uzo(TextNode):
    def to_text(self):
        return super().to_text() + ' '


class Dif(TextNode):
    pass


class Tezrad(Node):
    def to_text(self):
        return ''


# TODO link to url
class Url(TextNode):
    pass


# TODO link
class Lstref(TextNode):
    pass


class Trd(TextNode):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.lng = node.get('lng')

    # abel.xml has a trd inside a dif
    def to_text(self):
        if self.parent.tag == 'dif':
            return super().to_text()
        return ''


class Trdgrp(Node):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.lng = node.get('lng')

    def to_text(self):
        return ''


class Ref(TextNode):
    def __init__(self,node, extra_info=None):
        super().__init__(node, extra_info)
        self.tip = node.get('tip')

    def to_text(self):
        # TODO hide arrow
        symbol = "→"
        if self.tip == 'malprt':
            symbol = "↗"
        elif self.tip == "prt":
            symbol = "↘"
        content = StringWithFormat(symbol+' ')
        content += super().to_text()
        return content


class Refgrp(TextNode):
    pass


class Sncref(TextNode):
    pass


class Ekz(TextNode):
    base_format = Format.ITALIC


class Tld(Node):
    def __init__(self, node, extra_info=None):
        self.radix = None
        if extra_info:
            self.radix = extra_info.get('radix')

    def to_text(self):
        return self.radix or '-----'

# found in amik.xml
class Klr(TextNode):
    pass


class Rim(TextNode):
    def __init__(self, node, extra_info=None):
        super().__init__(node, extra_info)
        self.num = node.get('num') or ''

    def to_text(self):
        string = super().to_text()
        if self.num:
            return "Rim. %s: %s" % (self.num, string)
        return "Rim. %s" % string


class Aut(TextNode):
    def to_text(self):
        return "[%s]" % super().to_text()


class Fnt(Node):
    def to_text(self):
        return ''

# found in zon.xml
class Frm(TextNode):
    pass


# TODO sub format (seen en acetil.xml)
class Sub(TextNode):
    pass


class Sup(TextNode):
    pass


class K(TextNode):
    pass


class G(TextNode):
    pass


# TODO bold format (example: abstrakta)
class Em(TextNode):
    pass


class Ctl(TextNode):
    pass


class Ind(TextNode):
    pass


class Mll(TextNode):
    pass


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
