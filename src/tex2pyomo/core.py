"""Here's what I want:

Input is a tex file, written up as if to submit to a math opt journal,
with minimal formatting for ingestion to this kind of tool:

Output is a py file, which contains my mathematical model encoded in pyomo
objects, so that I can simply point it to data, or embed it in a larger
solve/iteration (i.e. a function which returns my model)

The main function should
- read in the input tex file, containing a number of tables to parse
  - specify subsection or keyword to filter by to only get the 5-ish tables we want???
- tex -> html -> {name: df}
- reformat each df's math as sympy
  - may need to generalize some of sympy to work with latex parser??
- map df/sympy to pyomo object
- write out the output file, containing a py function returning our encoded model

examples:

NOTE: need latex substitutions (for sympy parsing) as well as sympy mapping (for pyomo formulation)
latex substitutions just prior to sympy parsing:
- _+ -> _{\\nonneg} or _{\\pos}
- \Re -> Re (OK, ie. automatic at this point)
- _{j \in J} -> _{j = 1}^{|J|} or _{j = J}^J??
- _{ij} -> -{\ij} // weird how ij -> i*j in index

sympy->pyomo

# Set (Name, Index, Domain, Descripion) #

A set I:
- latex : $I$ & & & blah
- pandas: '\(I\)'
- sympy : Symbol('I')
- pyomo : I = Set()

A set K, indexed by i in I, with each K_i being a subset of J:
- latex : $K$ & $I$ & $J$ & blah
- pandas: '\(K\)'...
- sympy : Symbol('K')...
- pyomo : K = Set(I, within=J)

# Param (Name, Index, Domain, Description) #

A non-negative vector c, indexed by j in J
- latex : $c$ & $J$ & $\Re_+$ & blah // NOTE: _+ not allowed, use _{\pos} or _{\\nonneg}?
- pandas: '\(c\)'...
- sympy : Symbol('c'), Symbol('J'), Symbol('Re_{pos}')???
- pyomo : c = Param(J, within=NonNegativeReals)

A matrix A, indexed by i in I, j in J
- latex : $A$ & $I \times J$ & $\Re$ & blah
- pandas: '\(A\)'...
- sympy : Symbol('c'), Mul(Symbol('I'), Symbol('J')), Symbol('Re')
- pyomo : A = Param(I, J, within=Reals)

# Var (Name, Index, Domain, Description) #

A binary decision variable vector x, indexed by j in J
- latex : $x$ & $J$ & $\{0, 1\}$ & blah
- pandas: '\(x\)'...
- sympy : Symbol('x'), Symbol('J'), Symbol('Binary')???
- pyomo : x = Var(J, within=Binary)

# Objective (Name, Sense, Rule, Description) #

Only objective function:
- latex : $z$ & $\min$ & $\sum_{j \in J} c_j x_j
- pandas: '\(min\)'...
- sympy : Symbol('min'), 
   Sum(Mul(Symbol('c_{j}'), Symbol('x_{j}')), Tuple(Symbol('j'), Integer(1), Abs(Symbol('J'))))
   or Sum(Mul(Symbol('c_{j}'), Symbol('x_{j}')), Tuple(Symbol('j'), Symbol('J'), Symbol('J')))"
- pyomo : z = Objective(sense=minimize, rule=rule)
   def z_rule(m): return sum(m.c[j]*m.x[j] for j in m.J)

# Constraint (Name, Index, Rule, Description) #

row constraint:
- latex : $cons$ & $I$ & $\sum_{j \in J} A_{ij} x_j \geq b_i
- pandas: '\(cons\)'
- sympy : Symbol('cons'), 
   "GreaterThan(Sum(Mul(Symbol('A_{ij}'), Symbol('x_{j}')), Tuple(Symbol('j'), Integer(1), Abs(Symbol('J')))), Symbol('b_{i}'))"
- pyomo : cons = Constraint(I, rule=rule)
   def cons_rule(m, i): return sum(m.A[i, j]*m.x[j] for j in m.J) >= m.b[i]

"""
from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd
import pathlib
import subprocess
from sympy.parsing.latex import parse_latex
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
            print(f'*** {i} {label}')
            print(df)
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
        if table.label is not None:
            return str(table.label.string)
        else:
            return super(TexSoupifier, self).get_table_id(table)
    
    def table_to_df(self, table):
        # return super(TexSoupifier, self).table_to_df(table)
        # convert to html using pandoc without writing to file all right here
        test_cmd = ['pandoc', '-v']
        subprocess.run(test_cmd, capture_output=True)
        cmd = ['pandoc', '-f', 'latex', '-t', 'html', '--mathjax']
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            text=True,
            input=str(table),
        )
        df = HtmlSoupifier().table_to_df(res.stdout)
        return df
        

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
            subprocess.run(test_cmd, capture_output=True)
            subprocess.run(cmd)
        else:
            pass # not overwriting since it doesn't yet exist
    else:
        subprocess.run(test_cmd, capture_output=True)
        subprocess.run(cmd)
    output = html.check_file(output)
    return output


# NOT QUITE RIGHT, as texsoup doesn't seem to return tabulars in same order as html!?
# def read_dfs(path):
#     # given a file of ext either .tex or .html, return map of id to tables dataframed
#     # if html, do as is, but if tex, use tex for ids and revert to html for dfs
#     path = pathlib.Path(path)
#     if path.suffix == '.tex':
#         # use .tex read_dfs only to get ordered list of \labels
#         tex = path
#         _dfs = TexSoupifier().read_dfs(tex)
#         # names = _dfs.keys()
#         # then generate html if not already in existence
#         html = html_from_tex(tex, overwrite=False)
#     else:
#         _dfs = None
#         html = path
#     # either way use html to gather actual dfs, but rename if taken tex as input earlier
#     dfs = HtmlSoupifier().read_dfs(html)
#     if _dfs is not None:
#         assert len(_dfs) == len(dfs)
#         dfs = {k: df for (k, _), (_, df) in zip(_dfs.items(), dfs.items())}
#     return dfs


def main_tex():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    path = HERE.parent.parent / 'tests' / 'data' / 'test1.tex'
    print(f'{path=}')
    dfs = TexSoupifier().read_dfs(path)
    # for i, df in dfs.items():
    #     print('***', i)
    #     print(df)
  
      
def main_html():
    # mainly used to preliminary prints/testing of other package/my package's functionality
    HERE = pathlib.Path(__file__).parent
    path = HERE.parent.parent / 'tests' / 'data' / 'test1.html'
    print(f'{path=}')
    dfs = HtmlSoupifier().read_dfs(path)
    for i, df in dfs.items():
        print('***', i)
        print(df)


if __name__ == "__main__":
    main_tex()