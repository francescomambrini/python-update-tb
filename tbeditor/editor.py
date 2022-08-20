import conllu
import udapi
import pydotplus
from udapi.core.document import Document
from nltk.parse.dependencygraph import DependencyGraph

pos_dotcolor_map = {
    "ADJ" : "dodgerblue2",
    "ADP" : "darkgreen",
    "ADV" : "darkgoldenrod1",
    "AUX" : "darkolivegreen1",
    "CCONJ" : "deeppink",
    "DET" : "darkturquoise",
    "INTJ" : "gold",
    "NOUN" : "cyan4",
    "NUM" : "burlywood",
    "PART" : "darksalmon",
    "PRON" : "darkviolet",
    "PROPN" : "cornflowerblue",
    "PUNCT" : "dimgray",
    "SCONJ" : "chartreuse4",
    "SYM" : "gainsboro",
    "VERB" : "firebrick3",
    "X" : "gray16",
}


def parse_conllu_file(path):
    with open(path) as f:
        txt = f.read()
    try:
        c = conllu.parse(txt)
    except conllu.exceptions.ParseException:
        txt = txt.replace('    ', '\t')
        c = conllu.parse(txt)
    return c

def make_dg_tree(toklist: "conllu.TokenList") -> "DependencyGraph":
    tstr = "\n".join([f'{t["form"]}\t\
                        {t["upos"]}\t\
                        {t["head"]}\t\
                        {t["deprel"]}' for t in toklist if type(t['id']) is int])
    return DependencyGraph(tstr, top_relation_label='root')

def display_dg_tree(tokenlist: "conllu.TokenList") -> None:
    from IPython.display import display, Image

    dggraph = make_dg_tree(tokenlist)
    dot_tree = pydotplus.graph_from_dot_data(dggraph.to_dot())
    png = dot_tree.create_png()
    display(Image(png))

def delete_node(toklist: "conllu.TokenList", tok_to_del: "int", children='rehang_warn') -> "conllu.TokenList":
    doc = Document()
    doc.from_conllu_string(toklist.serialize())
    tree = next(doc.trees)
    try:
        t = [t for t in tree.descendants if t.ord == tok_to_del][0]
    except IndexError:
        raise ValueError(f"Token {tok_to_del} not found in sentence")
    else:
        t.remove(children=children)
    sent = conllu.parse(doc.to_conllu_string())
    return sent[0]

def add_empty_node(toklist: "conllu.TokenList", empty_ord: "float", **kwargs) -> "conllu.TokenList":
    doc = Document()
    doc.from_conllu_string(toklist.serialize())
    tree = next(doc.trees)
    newnode = tree.create_empty_child(**kwargs)
    newnode._ord = empty_ord

    sent = conllu.parse(doc.to_conllu_string())
    return sent[0]

def delete_empty_node(toklist: "conllu.TokenList", tok_to_del: "float") -> "conllu.TokenList":
    doc = Document()
    doc.from_conllu_string(toklist.serialize())
    tree = next(doc.trees)
    for i,e in enumerate(tree.empty_nodes):
        if e.ord == 8.1:
            tree.empty_nodes.pop(i)

    sent = conllu.parse(doc.to_conllu_string())[0]
    for t in sent:
        for i,d in enumerate(t['deps']):
            if type(d[1]) is tuple:
                if ''.join(d[1]) == str(tok_to_del):
                    t["deps"].pop(i)
    return sent

def clear_deps(toklist:  "conllu.TokenList") -> "conllu.TokenList":
    for tok in toklist:
        tok['deps'] = None
    return toklist

def copy_deps(toklist:  "conllu.TokenList") -> "conllu.TokenList":
    for tok in toklist:
        if tok['deps'] == None and tok['head'] != None:
            tok['deps'] = [(tok['deprel'], tok['head'])]
    return toklist

def get_id(el_id):
    if type(el_id) is tuple:
        return "".join([str(e) for e in el_id])
    else:
        return str(el_id)

def deps_to_dot(toklist: "conllu.TokenList") -> "str":
    dot_str = '''digraph G{
    bgcolor="snow1"
    edge [dir=forward color="gray56" style="dashed"]
    node [shape=plaintext]

    0 [label="Root (0)" fontcolor="midnightblue"]

    '''

    for node in toklist:
        nid = get_id(node['id'])
        upos = node['upos']
        color = pos_dotcolor_map.get(upos, 'gray16')
        form = node['form']
        if '-' in nid:
            continue
        dot_str += f'{nid} [label="{form}" fontcolor="{color}"]\n'
        
    for tok in toklist:
        nid = get_id(tok['id'])
        deps = tok['deps']
        if not deps:
            return 'digraph  {not -> available}'
        for dep in deps:
            dip = get_id(dep[1])
            dot_str += f'{dip} -> {nid} [label="{dep[0]}"]\n'
    dot_str += '}'

    return dot_str

def deprel_to_dot(toklist: "conllu.TokenList") -> "str":
    dot_str = '''digraph G{
    bgcolor="snow1"
    edge [dir=forward color="gray56" style="solid"]
    node [shape=plaintext]

    0 [label="Root (0)" fontcolor="midnightblue"]

    '''

    for node in toklist:
        nid = get_id(node['id'])
        upos = node['upos']
        color = pos_dotcolor_map.get(upos, 'gray16')
        form = node['form']
        if '-' in nid or '.' in nid:
            continue
        dot_str += f'{nid} [label="{form}" fontcolor="{color}"]\n'
        
    for tok in toklist:
        nid = get_id(tok['id'])
        if '.' in nid:
            continue
        head = tok['head']
        deprel = tok['deprel']
        dot_str += f'{head} -> {nid} [label="{deprel}"]\n'
        
    dot_str += '}'

    return dot_str