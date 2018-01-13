from enum import Enum


class Format(Enum):
    ITALIC = 'italic'
    BOLD = 'bold'


class StringWithFormat:
    def __init__(self, string=None):
        self.string = string or ''
        self.format = {}

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

    def add(self, other, format_type=None, keep_whitespace=False):
        # print('ADD', repr(self), repr(self.format), repr(other), format_type)
        if format_type and format_type.value not in self.format:
            self.format[format_type.value] = []

        if isinstance(other, StringWithFormat):
            assert format_type is None
            n = len(self.string)
            self.add(other.string, keep_whitespace=keep_whitespace)
            for fmt, fmt_list in other.format.items():
                if fmt not in self.format:
                    self.format[fmt] = []
                self.format[fmt] += [tuple(map(lambda x: x+n, indexes)) for indexes in fmt_list]
        else:
            if format_type:
                self.format[format_type.value].append((len(self.string), len(self.string) + len(other)))
            self.string += other
        return self

    def add_italic(self, other):
        return self.add(other, Format.ITALIC)

    def add_bold(self, other):
        return self.add(other, Format.BOLD)

    def apply_format(self, format_type):
        if not format_type:
            return self
        if format_type and format_type.value not in self.format:
            self.format[format_type.value] = []
        self.format[format_type.value].append((0, len(self.string)))
        return self

    def __add__(self, other):
        return self.add(other)

    def prepend(self, other):
        alt = StringWithFormat(other).add(self)
        self.string = alt.string
        self.format = alt.format
        return self

    def strip(self):
        original = self.string
        base_len = len(original)
        new_format = dict(self.format)

        new_string = original.rstrip()
        if len(new_string) != base_len:
            for key in new_format:
                new_format[key] = [ (a, min(len(new_string), b)) for (a,b) in new_format[key]]

        base_len = len(new_string)
        new_string = new_string.lstrip()
        if len(new_string) != base_len:
            dif = base_len - len(new_string)
            for key in new_format:
                new_format[key] = [
                    (max(0, a - dif), max(0, b - dif))
                    for (a,b) in new_format[key]]

        new_string_format = StringWithFormat(new_string)
        new_string_format.format = new_format
        return new_string_format

    def encode_format(self):
        encoded = []
        for fmt, values in self.format.items():
            tmp_list = ['%s,%s' % item for item in values]
            encoded.append("%s:%s" % (fmt, ';'.join(tmp_list)))
        return '\n'.join(encoded)

    def __eq__(self, other):
        if isinstance(other, StringWithFormat):
            return self.string == other.string and self.format == other.format
        return False

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.string))

    def __len__(self):
        return len(self.string)
