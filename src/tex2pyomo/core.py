from curses.ascii import HT
from bs4 import BeautifulSoup
from collections import OrderedDict
from dataclasses import dataclass
import pandas as pd
import pathlib
import subprocess
import sympy
from TexSoup import TexSoup

class FileParser(object):
    def __init__(self, suffix=None):
        self.suffix = suffix
    
    def check_file(self, path):
        # given a path to an (arbitrarily suffixed) file, check it exists, return pathlibified path
        path = pathlib.Path(path)
        assert path.is_file(), f'oops, {path=} is not (already) a file (cwd = {pathlib.Path.cwd()}'
        if self.suffix is not None:
            assert path.suffix == self.suffix, f'oops, {path.suffix=} is required to be {self.suffix=}'
        return path
            
    def read_file(self, path):
        # given a path to an (arbitrarily suffixed) file, check it and return its stringified contents
        path = self.check_file(path)
        with open(path, mode='r') as fh:
            res = fh.read()
        return res

class FileSoupifier(FileParser):
    def __init__(self, suffix=None, SoupClass=None, soup_kwargs=None):
        # suffix = suffix if suffix == '.tex' else '.html'
        super(FileSoupifier, self).__init__(suffix=suffix)
        # self.SoupClass = TexSoup if suffix == '.tex' else BeautifulSoup
        # TODO: assert something like SoupClass exists in this scope?
        self.SoupClass = SoupClass
        self.soup_kwargs = dict() if soup_kwargs is None else soup_kwargs

    def soupify(self, path):
        # given string contents (res) of file, return soupified version
        res = self.read_file(path)
        return self.SoupClass(res, **self.soup_kwargs)
    
    def read_dfs(self, path):
        dct = OrderedDict()
        soup = self.soupify(path)
        tables = self.find_tables(soup)
        for i, table in enumerate(tables):
            # form label
            label = self.get_table_id(table)
            if label is None:
                label = f'Table{i}'
            assert label not in dct, f'oops, {label=} should not be duplicated in tabular labels'
            # form df
            df = self.table_to_df(table)
            dct[label] = df
        return dct
    
    def find_tables(self, soup):
        # given soupified contents, return list of soupified tables (tabulars) found
        return soup.find_all('table')
    
    def get_table_id(self, table):
        # given soupified table, determine an id of the table
        return None
    
    def table_to_df(self, table):
        # given soupified table, return dataframified table
        return pd.DataFrame()
        
    
class TexSoupifier(FileSoupifier):
    def __init__(self):
        super(TexSoupifier, self).__init__(
            suffix='.tex',
            SoupClass=TexSoup,
        )

    def find_tables(self, soup):
        # given soupified contents, return list of soupified tables (tabulars) found
        return soup.find_all('tabular')
    
    def get_table_id(self, table):
        # given soupified table, determine an id of the table
        return str(table.label.string)
    
    # def table_to_df(self, table):
    #     return ??? # TODO: update
    

class HtmlSoupifier(FileSoupifier):
    def __init__(self):
        super(HtmlSoupifier, self).__init__(
            suffix='.html', 
            SoupClass=BeautifulSoup,
            soup_kwargs={
                'parser': 'html.parser',
                'features': 'lxml',
            }
        )
    
    def table_to_df(self, table):
        dfs = pd.read_html(str(table))
        assert len(dfs) == 1, f"oops, table should only be soup with 1 table, found {len(table)}:\n{table=}"
        df = dfs[0]
        return df


def html_from_tex(tex_path, overwrite=False):
    # given a path to a tex file, use pandoc+mathjax to convert it to html
    # and return resulting file's path
    tex = TexSoupifier()
    html = HtmlSoupifier()
    source = tex.check_file(tex_path)
    output = pathlib.Path(str(source).replace(tex.suffix, html.suffix))
    # TODO: perform check if pandoc exists; if not, exit this and return error, else continue
    test_cmd = ['pandoc', '-v']
    cmd = ['pandoc', '-s', str(source), '-o', str(output), '--mathjax']
    if output.is_file():
        if overwrite:
            print(f'WARNING: overwriting {output=}')
            subprocess.run(test_cmd)
            subprocess.run(cmd)
        else:
            pass # not overwriting since it doesn't yet exist
    else:
        subprocess.run(test_cmd)
        subprocess.run(cmd)
    output = html.check_file(output)
    return output


def read_dfs(path):
    # given a file of ext either .tex or .html, return map of id to tables dataframed
    # if html, do as is, but if tex, use tex for ids and revert to html for dfs
    path = pathlib.Path(path)
    if path.suffix == '.tex':
        # use .tex read_dfs only to get ordered list of \labels
        tex = path
        _dfs = TexSoupifier().read_dfs(tex)
        names = _dfs.keys()
        # then generate html if not already in existence
        html = html_from_tex(tex)
    else:
        names = None
        html = path
    # either way use html to gather actual dfs, but rename if taken tex as input earlier
    dfs = HtmlSoupifier().read_dfs(html)
    if names is not None:
        assert len(names) == len(dfs)
        dfs = {k: df for k, (_, df) in zip(names, dfs.items())}
    return dfs


def main_tex():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    path = HERE.parent.parent / 'tests' / 'data' / 'test1.tex'
    print(f'{path=}')
    dfs = read_dfs(path)
    for i, df in dfs.items():
        print('***', i)
        print(df)
        
def main_html():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    path = HERE.parent.parent / 'tests' / 'data' / 'test1.html'
    print(f'{path=}')
    dfs = read_dfs(path)
    for i, df in dfs.items():
        print('***', i)
        print(df)
        
def main():
    pass
    
if __name__ == "__main__":
    main_tex()