import os.path
import fire
import xml.etree.ElementTree as ET
from lxml import etree
from ..utils import add_hats, letter_enumerate
from .string_with_format import StringWithFormat, Format
from abc import abstractmethod
from typing import Union, Iterator, Optional, Type, TypeVar, cast


T = TypeVar("T", bound="Node")


def remove_extra_whitespace(string: str) -> str:
    cleaned = " ".join(string.split())
    # Preserve trailing whitespace
    if string and string[-1] == " ":
        cleaned += " "
    if string and string[0] == " ":
        cleaned = " " + cleaned
    return cleaned


class Node:
    def __init__(
        self, node: ET.Element, extra_info: Optional[dict[str, "Node"]] = None
    ):
        if extra_info is None:
            extra_info = {}
        self.parent: Optional["Node"] = extra_info.get("parent")
        self.children: list[Union[str, "Node"]]
        self.parse_children(node, extra_info)

    def __repr__(self):
        keys = " ".join(
            "{}={}".format(k, repr(v))
            for k, v in self.__dict__.items()
            if k != "parent"
        )
        return "<%s %s>" % (self.__class__.__name__, keys)

    def parse_children(self, node: ET.Element, extra_info: dict[str, "Node"]) -> None:
        self.children = []
        if node.text and node.text.strip():
            self.children.append(remove_extra_whitespace(node.text))
        for child in node:
            if child.tag in ["adm", "bld", "fnt"]:
                if child.tail and child.tail.strip():
                    self.children.append(remove_extra_whitespace(child.tail))
                continue
            tag_class = globals()[child.tag.title()]
            extra_info["parent"] = self
            self.children.append(tag_class(child, extra_info))
            if child.tail and child.tail.strip():
                self.children.append(remove_extra_whitespace(child.tail))
        self.children = self.add_whitespace_nodes_to_children()
        # print(node.tag, '- children:', self.children)

    def add_whitespace_nodes_to_children(self) -> list[Union[str, "Node"]]:
        children = []
        for n, child in enumerate(self.children):
            children.append(child)
            if isinstance(child, Ref) and n < len(self.children) - 1:
                next_node = self.children[n + 1]
                # print("DETECTED ref, next:", next_node, next_node.__class__)
                if isinstance(next_node, str) and next_node[0] not in ". ,;:":
                    children.append(" ")
                elif not isinstance(next_node, str):
                    children.append(" ")
            elif (
                isinstance(child, Klr) and n < len(self.children) - 1 and child.children
            ):
                if (
                    isinstance(child.children[-1], str)
                    and child.children[-1][-1] != " "
                ):
                    children.append(" ")
        return children

    def get(self, *args: Type[T]) -> Iterator[T]:
        "Get nodes based on their class"
        for tag in self.children:
            if tag.__class__ in args:
                tag = cast(T, tag)
                yield tag

    def get_except(self, *args: Type["Node"]) -> Iterator[Union[str, "Node"]]:
        for tag in self.children:
            if tag.__class__ not in args:
                yield tag

    def get_recursive(self, *args: Type[T]) -> Iterator[T]:
        if not hasattr(self, "children"):
            return
        for tag in self.children:
            if tag.__class__ in args:
                tag = cast(T, tag)
                yield tag
            elif isinstance(tag, str):
                continue
            else:
                for nested_tag in tag.get_recursive(*args):
                    yield nested_tag

    def get_ancestor(self, *args: Type[T]) -> T:
        if not self.parent:
            raise
        elif self.parent.__class__ in args:
            parent = cast(T, self.parent)
            return parent
        return self.parent.get_ancestor(*args)

    @abstractmethod
    def to_text(self) -> StringWithFormat:
        pass

    def main_word(self) -> str:
        kap = getattr(self, "kap", "")
        if not kap:
            kap = self.get_ancestor(Art).kap[0]
        if kap is None:
            return ""
        return add_hats(kap.strip())

    def translations(self) -> dict[str, dict[str, dict[Optional[int], list[str]]]]:
        trds: dict[str, dict[str, dict[Optional[int], list[str]]]] = {}
        for tag in self.get_recursive(Trd, Trdgrp):
            if not isinstance(tag.parent, (Drv, Snc)):
                continue

            # N° of snc inside the Drv
            snc_index = None
            if isinstance(tag.parent, Snc):
                if not isinstance(tag.parent.parent, Drv):
                    # TODO check if we are missing something
                    # example: -ad (ad.xml and subdrv)
                    continue
                drv = tag.parent.parent
                main_word = drv.main_word()

                sncs = [t for t in drv.children if isinstance(t, Snc)]
                # If there is only one Snc we don't need to specify a snc_index
                if len(sncs) > 1:
                    snc_index = sncs.index(tag.parent) + 1
            else:
                main_word = tag.parent.main_word()
            if main_word not in trds:
                trds[main_word] = {}

            if not isinstance(tag, (Trd, Trdgrp)):
                raise
            lng, texts = tag.parse_trd()
            if isinstance(texts, str):
                texts = [texts]

            if lng not in trds[main_word]:
                trds[main_word][lng] = {}
            trds[main_word][lng][snc_index] = texts

        return trds


class TextNode(Node):
    # Format enum, can also be a list
    base_format: Union[list[Format], Format, None] = None

    def to_text(self) -> StringWithFormat:
        parts: list[StringWithFormat] = []
        for node in self.children:
            if isinstance(node, str):
                parts.append(StringWithFormat(node))
            else:
                parts.append(node.to_text())
        try:
            content = StringWithFormat()
            for part in parts:
                content += part
            # print(self.children, "\n", parts, "\n")
            return content.apply_format(self.base_format)
        except Exception:
            print(self.children)
            print(parts)
            raise


class Art(Node):
    def __init__(self, node: ET.Element, extra_info=None):
        if extra_info is None:
            extra_info = {}
        assert node.tag == "art"
        rad = node.find("kap/rad")
        if rad is None:
            raise
        tail = ""
        if rad.tail:
            tail = rad.tail.strip()
        self.kap = (rad.text, tail)
        extra_info["radix"] = self.kap[0]
        super().__init__(node, extra_info)

    def derivations(self) -> Iterator[Union["Subart", "Drv"]]:
        for subart in self.get(Subart):
            for drv in subart.derivations():
                yield drv
        for drv in self.get(Drv):
            yield drv
        assert not list(self.get(Snc))

    def to_text(self):
        raise Exception("Do not use Art.to_text() directly")


class Kap(TextNode):
    pass


class Rad(TextNode):
    pass


class Gra(TextNode):
    pass


class Mlg(TextNode):
    pass


class Vspec(TextNode):
    def to_text(self) -> StringWithFormat:
        return StringWithFormat("(").add(super().to_text()).add(")")


class Ofc(TextNode):
    def to_text(self) -> StringWithFormat:
        return StringWithFormat("")


class Var(TextNode):
    pass


class Subart(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.mrk = ""
        self.kap = ""

    def derivations(self) -> Iterator[Union["Subart", "Drv"]]:
        # Note that this method sometimes will return the subart node
        drvs = list(self.get(Drv))
        if len(drvs) == 1:
            self.kap = drvs[0].kap
            self.mrk = drvs[0].mrk
            yield self
        else:
            for drv in drvs:
                if not self.kap:
                    self.kap = drv.kap
                    self.mrk = drv.mrk
                yield drv
        # al.xml, last <subart> has <snc> as a direct child
        if not drvs and list(self.get(Snc)):
            yield self


class Drv(Node):
    def __init__(self, node: ET.Element, extra_info=None):
        self.mrk = node.get("mrk") or ""
        if not extra_info:
            extra_info = {}
        kap_node = node.find("kap")
        assert kap_node is not None
        kap = Kap(kap_node, extra_info)
        self.kap = kap.to_text().string
        super().__init__(node, extra_info)
        self.parse_children(node, extra_info)

    def read_snc(self) -> list[StringWithFormat]:
        meanings = []
        n_sncs = len(list(self.get(Snc)))
        for n, snc in enumerate(self.get(Snc)):
            if n_sncs > 1:
                text = StringWithFormat("%s. " % (n + 1,))
                text += snc.to_text()
            else:
                text = snc.to_text()
            meanings.append(text)
        return meanings

    def to_text(self) -> StringWithFormat:
        content = StringWithFormat()

        # Kap and Fnt ignored
        for node in self.get(Gra, Uzo, Dif, Ref):
            if isinstance(node, Ref) and node.tip != "dif":
                continue
            content += node.to_text()
            if isinstance(node, Gra):
                content += " "

        meanings = self.read_snc()

        for nn, subdrv in letter_enumerate(self.get(Subdrv)):
            text = subdrv.to_text()
            text.prepend("%s. " % nn.upper())
            if nn == "a" and (meanings or len(content)):
                text.prepend("\n\n")
            meanings.append(text)

        content += StringWithFormat.join(meanings, "\n\n")

        # Renaming node2 to node causes issues with mypy
        for node2 in self.get_except(Subdrv, Snc, Gra, Uzo, Fnt, Kap, Dif, Mlg):
            if isinstance(node2, Ref) and node2.tip == "dif":
                continue
            if isinstance(node2, str):
                # Nodes added by hand in add_whitespace_nodes_to_children
                content += node2
            else:
                content += node2.to_text()

        return content


class Subdrv(Node):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.parse_children(node, extra_info)

    def to_text(self) -> StringWithFormat:
        content = StringWithFormat()

        # Fnt omitted
        for node in self.get(Dif, Gra, Uzo, Ref):
            if isinstance(node, Ref) and node.tip != "dif":
                continue
            content += node.to_text()

        for n, snc in enumerate(self.get(Snc), 1):
            text = snc.to_text()
            text.prepend("%s. " % n)
            text.prepend("\n\n")
            content += text

        for text_node in self.get_except(Snc, Gra, Uzo, Fnt, Dif, Ref):
            if isinstance(text_node, Ref) and text_node.tip == "dif":
                continue
            if isinstance(text_node, str):
                raise
            content += text_node.to_text()
        return content


class Snc(Node):
    def __init__(self, node, extra_info=None):
        self.mrk = node.get("mrk")
        if not extra_info:
            extra_info = {}
        # example: snc without mrk but drv has it (see zoni in zon.xml)
        self.mrk = self.mrk or extra_info["radix"]
        super().__init__(node, extra_info)

    def to_text(self) -> StringWithFormat:
        content = StringWithFormat()

        # Fnt ignored
        for node in self.get(Gra, Uzo, Dif, Ref):
            if isinstance(node, Ref) and node.tip != "dif":
                continue
            content += node.to_text()
            if isinstance(node, Gra):
                content += " "

        if list(self.get(Subsnc)):
            content += "\n\n"
            subs = []
            for n, subsnc in letter_enumerate(self.get(Subsnc)):
                text = subsnc.to_text()
                text.prepend("%s) " % n)
                subs.append(text)
            content += StringWithFormat.join(subs, "\n\n")

        # Renaming node2 to node causes issues with mypy
        for node2 in self.get_except(Gra, Uzo, Fnt, Dif, Subsnc):
            if isinstance(node2, Ref) and node2.tip == "dif":
                continue
            if isinstance(node2, str):
                # Nodes added by hand in add_whitespace_nodes_to_children
                content += node2
            else:
                content += node2.to_text()

        return content


class Subsnc(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.mrk = node.get("mrk")


class Uzo(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.tip = node.get("tip")
        if self.tip == "fak":
            self.base_format = Format.UZO_FAKO

    def to_text(self) -> StringWithFormat:
        text = super().to_text()
        if self.tip == "stl":
            mapping = {
                "FRAZ": "(frazaĵo)",
                "FIG": "(figure)",
                "VULG": "(vulgare)",
                "RAR": "(malofte)",
                "POE": "(poezie)",
                "ARK": "(arkaismo)",
                "EVI": "(evitinde)",
                "KOMUNE": "(komune)",
                "NEO": "(neologismo)",
            }
            text = StringWithFormat(mapping.get(text.string, text.string))
        return text + " "


class Dif(TextNode):
    pass


class Tezrad(Node):
    def to_text(self) -> StringWithFormat:
        return StringWithFormat("")


# TODO link to url
class Url(TextNode):
    pass


# TODO link
class Lstref(TextNode):
    pass


class Trd(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.lng = node.get("lng") or ""

    # abel.xml has a trd inside a dif
    def to_text(self) -> StringWithFormat:
        if isinstance(self.parent, Dif):
            return super().to_text()
        return StringWithFormat("")

    def parse_trd(self) -> tuple[str, str]:
        return (self.lng, super().to_text().string)


class Trdgrp(Node):
    def __init__(self, node: ET.Element, extra_info=None):
        self.lng = node.get("lng") or ""
        super().__init__(node, extra_info)

    def to_text(self) -> StringWithFormat:
        return StringWithFormat("")

    def parse_trd(self) -> tuple[str, list[str]]:
        return (self.lng, [trd.parse_trd()[1] for trd in self.get(Trd)])


class Ref(TextNode):
    @staticmethod
    def add_arrow(tip: Optional[str], text: StringWithFormat) -> StringWithFormat:
        if not tip:
            return text
        symbol = "→"
        if tip == "dif":
            symbol = "="
        content = StringWithFormat(symbol + " ")
        content += text
        return content

    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.tip = node.get("tip")

    def to_text(self) -> StringWithFormat:
        if isinstance(self.parent, (Dif, Rim, Ekz, Klr)):
            return super().to_text()
        return Ref.add_arrow(self.tip, super().to_text())

    #     symbol = "→"
    #     if self.tip == 'malprt':
    #         symbol = "↗"
    #     elif self.tip == "prt":
    #         symbol = "↘"
    #     content = StringWithFormat(symbol+' ')
    #     content += super().to_text()
    #     return content


class Refgrp(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.tip = node.get("tip")

    def to_text(self) -> StringWithFormat:
        if isinstance(self.parent, (Dif, Rim, Ekz, Klr)):
            return super().to_text()
        return Ref.add_arrow(self.tip, super().to_text())


class Sncref(TextNode):
    pass


class Ekz(TextNode):
    base_format = Format.EKZ

    def to_text(self) -> StringWithFormat:
        content = super().to_text()
        content.prepend("\n")
        return content


class Tld(Node):
    def __init__(self, node: ET.Element, extra_info=None):
        self.radix = ""
        self.lit = node.get("lit") or ""
        if extra_info:
            self.radix = extra_info.get("radix") or ""
        self.radix = self.radix.strip()
        self.parent = extra_info.get("parent")

    def to_text(self) -> StringWithFormat:
        content = None
        if self.lit and self.radix:
            content = StringWithFormat(self.lit + self.radix[1:])
        else:
            content = StringWithFormat(self.radix or "-----")
        if isinstance(self.parent, Ekz) or (
            self.parent and isinstance(self.parent.parent, Ekz)
        ):
            content = content.apply_format(Format.TLD)
        return content


# found in amik.xml
class Klr(TextNode):
    pass


class Rim(TextNode):
    def __init__(self, node: ET.Element, extra_info=None):
        super().__init__(node, extra_info)
        self.num = node.get("num") or ""

    def to_text(self) -> StringWithFormat:
        string = super().to_text()
        if self.num:
            content = StringWithFormat().add_bold("\n\nRim. %s: " % self.num)
            content += string
            return content
        return StringWithFormat().add_bold("\n\nRim. ").add(string)


class Aut(TextNode):
    def to_text(self) -> StringWithFormat:
        return StringWithFormat("[").add(super().to_text()).add("]")


class Fnt(Node):
    def to_text(self) -> StringWithFormat:
        return StringWithFormat("")


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


class Nom(TextNode):
    pass


class Esc(TextNode):
    pass


class Nac(TextNode):
    pass


class Baz(TextNode):
    pass


# seen in dank.xml, danke al
class Mis(TextNode):
    pass


# TODO strikethrough
class Ts(TextNode):
    pass


# https://github.com/sstangl/tuja-vortaro/blob/master/revo/convert-to-js.py
def entities_dict() -> dict[str, str]:
    entities: dict[str, str] = {}

    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "revo", "dtd")
    with open(os.path.join(base_dir, "vokosgn.dtd"), "rb") as f:
        dtd = etree.DTD(f)
        for entity in dtd.iterentities():
            entities[entity.name] = entity.content

    with open(os.path.join(base_dir, "vokourl.dtd"), "rb") as f:
        dtd = etree.DTD(f)
        for entity in dtd.iterentities():
            entities[entity.name] = entity.content

    with open(os.path.join(base_dir, "vokomll.dtd"), "rb") as f:
        dtd = etree.DTD(f)
        for entity in dtd.iterentities():
            entities[entity.name] = entity.content
    return entities


def parse_article(filename: str) -> Art:
    with open(filename) as f:
        article = f.read()

    xml_parser = ET.XMLParser()
    for entity, value in entities_dict().items():
        xml_parser.entity[entity] = value
    tree = ET.fromstring(article, parser=xml_parser)

    art = tree.find("art")
    if not art:
        raise Exception("XML file does not contain <art> tag!")
    return Art(art)


def main(word: str):
    art = parse_article("xml/%s.xml" % word)
    print(art)
    print()
    print(art.to_text())


if __name__ == "__main__":
    fire.Fire(main)
