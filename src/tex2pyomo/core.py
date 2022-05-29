from collections import OrderedDict
import os
import pandas as pd
import pathlib
from TexSoup import TexSoup

def read_file(path, suffix=None):
    # given a path to a file, return its stringified contents
    path = pathlib.Path(path)
    assert path.is_file(), f'oops, {path=} is not (already) a file (cwd = {pathlib.Path.cwd()}'
    if suffix is not None:
        assert path.suffix == suffix, f'oops, {path.suffix=} is required to be {suffix=}'
    with open(path, mode='r') as fh:
        res = fh.read()
    return res

# tex

def read_tex(path):
    # given a path to a LaTeX file, return its soupified contents
    res = read_file(path, suffix='.tex')
    soup = TexSoup(res)
    return soup

def get_tex_tables(soup):
    tables = soup.find_all('tabular')
    dct = OrderedDict()
    for i, t in enumerate(tables):
        # print('***', i, t)
        label = str(t.label.string)
        # print(f'{label=}')
        name = label if label is not None else f'Table{i}'
        assert name not in dct, f'oops, {name=} should not be duplicated in tabular labels'
        dct[name] = t
    return dct

def read_tex_tables(path):
    res = read_tex(path)
    dct = get_tex_tables(res)
    return dct

# html

def read_html_tables(path):
    # given a path to a file, returns its tables dataframe-ified
    return pd.read_html(path)

# converters

def tex_to_html(path, overwrite=False, suffix='.tex'):
    # given a path to a tex file, use pandoc+mathjax to convert it to html
    # and return resulting file's path
    path = pathlib.Path(path)
    assert path.is_file(), f'oops, {path=} is not (already) a file (cwd = {pathlib.Path.cwd()}'
    if suffix is not None:
        assert path.suffix == suffix, f'oops, {path.suffix=} is required to be {suffix=}'
    # with open(path, mode='r') as fh:
    #     res = fh.read()
    res_path = pathlib.Path(str(path).replace(path.suffix, '.html'))
    if res_path.is_file():
        if overwrite:
            print(f'WARNING: overwriting {res_path=}')
            # TODO: check that pandoc is installed?
            os.system(f'pandoc -v && pandoc -s {path} -o {res_path} --mathjax')
        else:
            pass # not overwriting since it doesn't yet exist
    else:
        # TODO: system call: pandoc -s test1.tex -o test1.html --mathjax        
        os.system(f'pandoc -v && pandoc -s {path} -o {res_path} --mathjax')
    assert res_path.is_file(), f'oops, {res_path=} is not (already) a file (cwd = {pathlib.Path.cwd()}'
    return res_path

def main():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    f = HERE.parent.parent / 'tests' / 'data' / 'test1.tex'
    print(f'{f=}')
    # soup = read_tex(f)
    tex_tables = read_tex_tables(f)
    if f.suffix == '.tex':
        dct = {}
        f = tex_to_html(f) # silently skipped if html exists
        print(f'{f=}')
        dfs = read_html_tables(f)
        # WARNING: assumes tex_tables ordered same as dfs (and same len?)
        assert len(tex_tables) == len(dfs)
        for i, ((label, table), df) in enumerate(zip(tex_tables.items(), dfs)):
            dct[label] = df
            # anything else needed from table?
            # print('***', i)
            # print(label)
            # print(df)
            # print(table)
        print(len(dct), dct.keys())
    
    
if __name__ == "__main__":
    main()