import os
import glob
import json
from lxml import etree
from typing import Dict, List, Optional, Tuple

# category, text, link
PmegLink = Tuple[Optional[str], str, str]


def parse_index_entry(tag) -> Tuple[str, List[PmegLink]]:
    headword: Optional[str] = None
    links: List[PmegLink] = []

    for child in tag:
        if child.tag == "strong":
            word: str = etree.tostring(child, method="text", encoding="utf-8").decode("utf-8")
            headword = word.strip().lower()
            # print(word)
        elif child.tag == "ul":
            ul_class = child.get('class')
            if ul_class == "chefligoj":
                for li in child.xpath(".//li"):
                    text = etree.tostring(li, method="text", encoding="utf-8").decode("utf-8").strip()
                    link = list(li.iter("a"))[0].get('href')
                    # print(link, text)
                    links.append((None, text, link))
            elif ul_class == "subvortoj":
                for li in child.xpath("./li"):
                    assert li.get('class') == 'subvorto'
                    category = li.text or etree.tostring(li[0], method="text", encoding="utf-8").decode("utf-8")
                    category = category.strip()
                    print(headword, len(list(li.iter('li'))))
                    for inner_li in li.xpath('./ul/li'):
                        text = etree.tostring(inner_li, method="text", encoding="utf-8").decode("utf-8").strip()
                        link = list(inner_li.iter("a"))[0].get('href')
                        links.append((category, text, link))
            else:
                raise

        else:
            raise

    if headword is None:
        raise

    return (headword, links)


def process() -> None:
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'pmeg')
    parser = etree.HTMLParser()
    index_files = glob.glob(os.path.join(base_dir, '*.html'))
    index_files.sort()

    pmeg_entry: Dict[str, List[PmegLink]] = {}

    for index_file in index_files:
        print(index_file)
        with open(index_file, 'rb') as f:
            tree = etree.parse(f, parser)
            for tag in tree.xpath("//li[@class='art'][./strong[@class='chefvorto']/i]"):
                headword, links = parse_index_entry(tag)

                for single_headword in headword.split(","):
                    pmeg_entry[single_headword.strip()] = links

    with open(os.path.join(base_dir, 'pmeg_index.json'), 'w', encoding="utf-8") as f:
        json.dump(pmeg_entry, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    process()