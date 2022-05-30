from curses.ascii import HT
from bs4 import BeautifulSoup
from collections import OrderedDict
from dataclasses import dataclass
import pandas as pd
import pathlib
import subprocess
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
    test_cmd = 'pandoc -v'
    cmd = f'pandoc -s {source} -o {output} --mathjax'
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


def main():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    tex = HERE.parent.parent / 'tests' / 'data' / 'test1.tex'
    print(f'{tex=}')
    # read dfs directly from tex
    tex_dfs = TexSoupifier().read_dfs(tex)
    for i, df in tex_dfs.items():
        print('***', i)
        print(df)
    html = html_from_tex(tex)
    print(f'{html=}')
    # read dfs directly from html
    html_dfs = HtmlSoupifier().read_dfs(html)
    for i, df in html_dfs.items():
        print('***', i)
        print(df)

    
if __name__ == "__main__":
    main()