"""
Parse InterPro flat files

Flat files:
ftp://ftp.ebi.ac.uk/pub/databases/interpro/interpro.xml.gz
ftp://ftp.ebi.ac.uk/pub/databases/interpro/ParentChildTreeFile.txt
ftp://ftp.ebi.ac.uk/pub/databases/interpro/protein2ipr.dat.gz

ParentChildTreeFile describes the relationships between items (that have relationships.
i.e. not all items are in this file). Use ifyou want levels. I wrote this before I wrote the xml parser.
This file isn't necesary.

protein2ipr.dat.gz contains annotations for each protein in uniprot

@author: gstupp
"""
import json
import os
import subprocess
from itertools import groupby
import gzip
import lxml.etree as et
from dateutil import parser as dup
import requests
from tqdm import tqdm

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class IPRTerm:
    """
    Represents one interproscan term/item

    """
    type2d = {"Active_site": "InterPro Active Site",
              "Binding_site": "InterPro Binding Site",
              "Conserved_site": "InterPro Conserved Site",
              "Domain": "InterPro Domain",
              "Family": "InterPro Family",
              "PTM": "InterPro PTM",
              "Repeat": "InterPro Repeat"}

    def __init__(self, name=None, short_name=None, id=None, parent=None, children=None, contains=None,
                 found_in=None, level=None, type=None, description=None, **kwargs):
        self.name = name
        self.short_name = short_name
        self.id = id
        self.parent = parent
        self.children = children
        self.contains = contains
        self.found_in = found_in
        self.level = level
        self.type = type
        self.description = description
        if self.description is None and self.type:
            self.description = IPRTerm.type2d[self.type]

    def __repr__(self):
        return '{}: {}'.format(self.id, self.name)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)


def parse_tree(tree_handle):
    """
    Parses ParentChildTreeFile.txt
    Looks like:
    IPR000276::G protein-coupled receptor, rhodopsin-like::
    --IPR002231::5-hydroxytryptamine receptor family::
    ----IPR000377::5-Hydroxytryptamine 2C receptor::
    ----IPR000455::5-Hydroxytryptamine 2A receptor::
    ----IPR000482::5-Hydroxytryptamine 2B receptor::
    :param tree_handle:
    :return:
    """
    prev_level = 0
    prev_parents = []
    d = {}

    for line in tree_handle:
        id_level, name, _ = line.strip().split('::')
        id = id_level[id_level.index('I'):]
        curr_level = int(id_level.count('-') / 2)

        if curr_level == 0:
            term = IPRTerm(id=id, name=name, parent=None, level=0)
            prev_parents = [term]

        elif curr_level > prev_level:
            term = IPRTerm(id=id, name=name, parent=prev_parents[-1], level=curr_level)
            prev_parents.append(term)

        elif curr_level < prev_level:
            for i in range(prev_level + 1 - curr_level):
                prev_parents.pop()
            term = IPRTerm(id=id, name=name, parent=prev_parents[-1], level=curr_level)
            prev_parents.append(term)

        elif curr_level == prev_level:
            prev_parents.pop()
            term = IPRTerm(id=id, name=name, parent=prev_parents[-1], level=curr_level)
            prev_parents.append(term)

        prev_level = curr_level
        d[term.id] = term

    # populate children
    for rec in d.values():
        if rec.parent:
            # this works because a child can only have one parent
            # and IPRTerm.parent is a reference to the IPRTerm object
            rec.parent.children.append(rec)

    return d


def get_unprot_ids_from_species(species_wdid):
    """
    # get all uniprot ids from species

    :return:
    """
    query = """PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        SELECT ?item ?id
        WHERE
        {
            ?item wdt:P279 wd:Q8054 .
            ?item wdt:P703 wd:{} .
            ?item wdt:P352 ?id
        }""".format(species_wdid)
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()

    human_uniprot = {x['id']['value']: x['item']['value'] for x in data['results']['bindings']}
    uniprot_ids = set(human_uniprot.keys())
    return uniprot_ids


def parse_protein2ipr(p2ipr_filename, keep_ids=None):
    """
    A0A060XN28	IPR029064	50S ribosomal protein L30e-like	SSF55315	17	101
    A0A060XN29	IPR003653	Ulp1 protease family, C-terminal catalytic domain	PF02902	412	581
    A0A060XN29	IPR003653	Ulp1 protease family, C-terminal catalytic domain	PS50600	397	562
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PF00001	1	234
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	28	49
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	72	95
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	174	198
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	216	242
    A0A060XN30	IPR000455	5-Hydroxytryptamine 2A receptor	PTHR24247:SF30	1	282
    A0A060XN30	IPR017452	GPCR, rhodopsin-like, 7TM	PS50262	1	234
    A0A060XN31	IPR004092	Mbt repeat	PF02820	50	117
    A0A060XN31	IPR004092	Mbt repeat	PS51079	1	114
    A0A060XN31	IPR004092	Mbt repeat	PS51079	122	196
    A0A060XN31	IPR004092	Mbt repeat	SM00561	23	114
    """

    p = subprocess.Popen(["zcat", p2ipr_filename], stdout=subprocess.PIPE).stdout
    uni_dict = {}
    p2ipr = map(lambda x: x.decode('utf-8').rstrip().split('\t'), p)
    for key, lines in tqdm(groupby(p2ipr, key=lambda x: x[0]), total=51536456):
        # the total is just for a time estimate. Nothing bad happens if the total is wrong
        if keep_ids and key not in keep_ids:
            continue
        protein = []
        for line in lines:
            uniprot_id, interpro_id, name, ext_id, start, stop = line
            protein.append({'uniprot_id': uniprot_id, 'interpro_id': interpro_id, 'name': name,
                            'ext_id': ext_id, 'start': start, 'stop': stop})
        uni_dict[key] = protein
    return uni_dict


def parse_human_protein_ipr():
    p2ipr_filename = os.path.join(DATA_DIR, "protein2ipr.dat.gz")
    uni_dict = parse_protein2ipr(p2ipr_filename, keep_ids=get_unprot_ids_from_species("Q5"))

    with open("interproscan_uniprot_human.json", 'w') as f:
        json.dump(uni_dict, f, indent=2)


def parse_interpro_xml():
    d = {}

    f = gzip.GzipFile("interproscan/data/interpro.xml.gz")
    parser = et.parse(f)
    root = parser.getroot()

    release_info = dict(root.find("release").find("dbinfo[@dbname='INTERPRO']").attrib)
    release_info['date'] = dup.parse(release_info['file_date'])

    for itemxml in root.findall("interpro"):
        item = IPRTerm(name = itemxml.find('name').text, **itemxml.attrib)
        parents = [x.attrib['ipr_ref'] for x in itemxml.find("parent_list").getchildren()] if itemxml.find("parent_list") is not None else None
        children = [x.attrib['ipr_ref'] for x in itemxml.find("child_list").getchildren()] if itemxml.find("child_list") is not None else None
        contains = [x.attrib['ipr_ref'] for x in itemxml.find("contains").getchildren()] if itemxml.find("contains") is not None else None
        found_in = [x.attrib['ipr_ref'] for x in itemxml.find("found_in").getchildren()] if itemxml.find("found_in") is not None else None
        if parents:
            assert len(parents) == 1
            item.parent = parents[0]
        item.children = children
        item.contains = contains
        item.found_in = found_in
        d[item.id] = item
    return d, release_info


"""
# stats
from .parser import parse_interproscan_items
d = parse_interproscan_items()
Counter([any([d[x['interpro_id']].type=="Family" for x in value]) for value in uni_dict.values()])
Counter([x.type for x in d.values() if x.id in human_ipr])
"""