from ..parser.string_with_format import StringWithFormat


def test_init():
    string = StringWithFormat()
    assert string.string == ''
    assert string.format == {}


def test_add():
    string = StringWithFormat()
    string.add('Saluton')
    assert string.string == 'Saluton'
    string.add(' mondo!')
    assert string.string == 'Saluton mondo!'

def test_add_format():
    string = StringWithFormat()
    string.add_italic('Saluton')
    assert string.string == 'Saluton'
    assert string.format == {'italic': [(0, 7)]}
    string.add_italic(' mondo!')
    assert string.string == 'Saluton mondo!'
    assert string.format == {'italic': [(0, 14)]}


def test_add_format_final():
    string = StringWithFormat()
    string.add('Saluton')
    assert string.string == 'Saluton'
    string.add_italic(' mondo!')
    assert string.string == 'Saluton mondo!'
    assert string.format == {'italic': [(7, 14)]}


def test_merge():
    string1 = StringWithFormat()
    string2 = StringWithFormat()
    string1.add_italic('N')
    string2.add_italic('u')
    string1.add(string2)
    assert string1.string == 'Nu'
    assert string1.format == {'italic': [(0, 2)]}


def test_prepend():
    string = StringWithFormat()
    string.add_italic('mondo!')
    assert string.format == {'italic': [(0, 6)]}
    string.prepend('Saluton ')
    assert string.string == 'Saluton mondo!'
    assert string.format == {'italic': [(8, 14)]}

def test_strip_left():
    string = StringWithFormat()
    string.add_italic('  Bonan tagon')
    string = string.strip()
    assert string.string == 'Bonan tagon'
    assert string.format ==  {'italic': [(0, 11)]}

def test_strip_right():
    string = StringWithFormat()
    string.add_italic('Bonan tagon  ')
    string = string.strip()
    assert string.string == 'Bonan tagon'
    assert string.format ==  {'italic': [(0, 11)]}

def test_join():
    s1 = StringWithFormat().add_italic('a')
    s2 = StringWithFormat('b')
    s3 = StringWithFormat().add_italic('c')
    string = StringWithFormat.join([s1, s2, s3], '-')
    assert string.string == 'a-b-c'
    assert string.format == {'italic': [(0, 1), (4, 5)]}

def test_encode_format():
    s = StringWithFormat().add_bold('Bonan').add_italic(' tagon').add_bold('!')
    assert s.encode_format() == 'bold:0,5;11,12\nitalic:5,11'
