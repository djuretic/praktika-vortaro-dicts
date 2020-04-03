from enum import Enum
from typing import Optional, Dict, List, Tuple, Union


class Format(Enum):
    ITALIC = 'italic'
    BOLD = 'bold'
    EKZ = 'ekz'
    TLD = 'tld'
    UZO_FAKO = 'fako'


class StringWithFormat:
    def __init__(self, string: Optional[str] = None):
        self.string = string or ''
        self.format: Dict = {}

    @classmethod
    def join(cls, string_list, separator):
        if len(string_list) == 0:
            return StringWithFormat()
        base = string_list[0]
        for n, string in enumerate(string_list[1:]):
            if n < len(string_list) - 1:
                base += separator
            base += string
        return base

    def add(self, other, format_type=None, keep_whitespace=False) -> 'StringWithFormat':
        # print('ADD', repr(self), repr(self.format), repr(other), format_type)
        if format_type and format_type.value not in self.format:
            self.format[format_type.value] = []

        if isinstance(other, StringWithFormat):
            assert format_type is None
            # first string length
            n = len(self.string)
            self.add(other.string, keep_whitespace=keep_whitespace)
            for fmt, fmt_list in other.format.items():
                if fmt not in self.format:
                    self.format[fmt] = []

                if self.format[fmt] and self.format[fmt][-1][-1] == n and \
                        fmt_list and fmt_list[0][0] == 0:
                    # merge two formats in one
                    self.format[fmt][-1] = (self.format[fmt][-1][0], n + fmt_list[0][1])
                    fmt_list = fmt_list[1:]
                self.format[fmt] += [tuple(map(lambda x: x+n, indexes)) for indexes in fmt_list]
        else:
            if format_type:
                last_format = self.format[format_type.value]
                if last_format and last_format[-1][-1] == len(self.string):
                    last_format[-1] = (last_format[-1][0], len(self.string) + len(other))
                else:
                    self.format[format_type.value].append((len(self.string), len(self.string) + len(other)))
            self.string += other
        return self

    def add_italic(self, other) -> 'StringWithFormat':
        return self.add(other, Format.ITALIC)

    def add_bold(self, other) -> 'StringWithFormat':
        return self.add(other, Format.BOLD)

    def apply_format(self, format_type: Union[List, Tuple, Format, None]) -> 'StringWithFormat':
        if not format_type:
            return self
        if isinstance(format_type, (list, tuple)):
            for format_t in format_type:
                self.apply_format(format_t)
        else:
            if format_type and format_type.value not in self.format:
                self.format[format_type.value] = []
            self.format[format_type.value].append((0, len(self.string)))
        return self

    def __add__(self, other) -> 'StringWithFormat':
        return self.add(other)

    def prepend(self, other) -> 'StringWithFormat':
        alt = StringWithFormat(other).add(self)
        self.string = alt.string
        self.format = alt.format
        return self

    def strip(self) -> 'StringWithFormat':
        original = self.string
        base_len = len(original)
        new_format = dict(self.format)

        new_string = original.rstrip()
        if len(new_string) != base_len:
            for key in new_format:
                new_format[key] = [(a, min(len(new_string), b)) for (a, b) in new_format[key]]

        base_len = len(new_string)
        new_string = new_string.lstrip()
        if len(new_string) != base_len:
            dif = base_len - len(new_string)
            for key in new_format:
                new_format[key] = [
                    (max(0, a - dif), max(0, b - dif))
                    for (a, b) in new_format[key]]

        new_string_format = StringWithFormat(new_string)
        new_string_format.format = new_format
        return new_string_format

    def encode_format(self) -> str:
        encoded = []
        for fmt, values in self.format.items():
            tmp_list = ['%s,%s' % item for item in values]
            encoded.append("%s:%s" % (fmt, ';'.join(tmp_list)))
        return '\n'.join(encoded)

    def __eq__(self, other) -> bool:
        if isinstance(other, StringWithFormat):
            return self.string == other.string and self.format == other.format
        return False

    def __repr__(self) -> str:
        return '<%s %s>' % (self.__class__.__name__, repr(self.string))

    def __len__(self) -> int:
        return len(self.string)


def expand_tld(string):
    if not isinstance(string, StringWithFormat) or not string.format.get(Format.TLD.value):
        return string
    boundaries = " \n:;;.,•?!()[]{}'\"„“"
    original_format = string.format[Format.TLD.value]
    new_format = []
    for start, end in original_format:
        for i in range(start, -1, -1):
            if string.string[i] in boundaries:
                break
            start = i
        for i in range(end, len(string.string)):
            end = i
            if string.string[i] in boundaries:
                break
        else:
            end = len(string.string)
        new_format.append((start, end))

    string.format[Format.TLD.value] = new_format
    return string
