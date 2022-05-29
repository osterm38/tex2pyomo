from tex2pyomo import read_tex
import pathlib

HERE = pathlib.Path(__file__).parent
TEST_FILE1 = HERE / 'data' / 'test1.tex'

def test_something():
    assert 2 + 2 == 4
    
def test_section():
    soup = read_tex(TEST_FILE1)
    print(soup)
    assert soup.section.string == 'Intro'
