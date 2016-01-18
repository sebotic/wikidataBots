import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
from SPARQLWrapper import SPARQLWrapper, JSON
import csv
import requests
import urllib.request
import pprint
import PBB_Core
import PBB_login
import ast
import time
from time import gmtime, strftime
import copy

__author__ = 'timputman'

#login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])


class WDProp2QID_SPARQL(object):
    def __init__(self, prop='', string=''):
        self.qid = self.SPARQL_for_qidbyprop(prop, string)

    def SPARQL_for_qidbyprop(self, prop, string):
        """
        :param prop: 'P351' Entrez gene id (ex. print( SPARQL_for_qidbyprop('P351','899959')))
        :param string: '899959' String value
        :return: QID Q21514037
        """
        sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        prefix = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/>'
        arguments = '?gene wdt:{} "{}"'.format(prop, string)
        select_where = 'SELECT * WHERE {{{}}}'.format(arguments)
        query = prefix + " " + select_where
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        final_qid =[]
        try:
            rawqid = results['results']['bindings'][0]['gene']['value']
            qid_list = rawqid.split('/')
            final_qid.append(qid_list[-1])
        except Exception:
            final_qid.append('None')
        return final_qid[0]


class WDQID2Label_SPARQL(object):
    def __init__(self, qid=''):
        self.label = self.qid2label(qid)

    def qid2label(self, qid):
        sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        prefix = 'PREFIX wd: <http://www.wikidata.org/entity/>'
        arguments = ' wd:{} rdfs:label ?label. Filter (LANG(?label) = "en") .'.format(qid)
        select_where = 'SELECT ?label WHERE {{{}}}'.format(arguments)
        query = prefix + " " + select_where
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        final_qid =[]
        try:
            rawqid = results['results']['bindings'][0]['label']['value']
            final_qid.append(rawqid)
        except Exception:
            final_qid.append('None')
        return final_qid[0]


class NCBIReferenceGenomes(object):
    def __init__(self):
        self.tid_list = self.get_ref_microbe_taxids()

    def get_ref_microbe_taxids(self):
        """
        Download the latest bacterial genome assembly summary from the NCBI genome ftp site
        and generate a list of relevant data for strain items based on taxids of the bacterial reference genomes.

        :return:
        """
        assembly = urllib.request.urlopen("ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt")
        datareader = csv.reader(assembly.read().decode().splitlines(), delimiter="\t")

        ref_org_list = []
        for row in datareader:
            if row[4] == 'reference genome':
                org = row[7].split()
                strain = " ".join(org[2:])
                genus = org[0]
                species = org[1]
                species_tid = row[6]
                strain_tid = row[5]
                organism_data = [species_tid, strain_tid, genus, species, strain]
                ref_org_list.append(organism_data)
        return ref_org_list


class MicrobeResources(object):

    def __init__(self, ref_org):
        self.species_tid = ref_org[0]
        self.strain_tid = ref_org[1]
        self.genus = ref_org[2]
        self.species = ref_org[3]
        self.strain = ref_org[4]
        self.organism = " ".join([self.genus, self.species, self.strain])
        self.gen_spec = " ".join([self.genus, self.species])
        self.gene_record = self.mygeneinfo_download()
        self.goterms = self.download_taxon_protein_GO()
        self.combined = self.combine_mgi_uniprot_dicts()

    def mygeneinfo_download(self):

        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=self.strain_tid, entrezonly="true", size="20", fields="all")
        r = requests.get(url=url, params=params)
        hits = r.json()
        strain_qid = WDProp2QID_SPARQL(prop='P685', string=self.strain_tid).qid
        strain_label = WDQID2Label_SPARQL(qid=strain_qid).label
        gene_description = "microbial gene found in " + strain_label
        protein_description = "microbial protein found in " + strain_label

        mgi_data = []

        for i in hits['hits']:
            if i['type_of_gene'] != 'protein-coding':
                continue
            else:
                uniprot = ''
                if 'uniprot' in i.keys():
                    if 'Swiss-Prot' in i['uniprot']:
                        if isinstance(i['uniprot']['Swiss-Prot'],str):
                            uniprot = i['uniprot']['Swiss-Prot']
                        else:
                            uniprot = i['uniprot']['Swiss-Prot'][0]

                    if 'TrEMBL' in i['uniprot']:
                        if isinstance(i['uniprot']['TrEMBL'],str):
                            uniprot = i['uniprot']['TrEMBL']
                        else:
                            uniprot = i['uniprot']['TrEMBL'][0]
                else:
                    continue

                wd_data = {
                    'species_taxid': str(self.species_tid),
                    'strain_taxid': str(self.strain_tid),
                    '_geneid': str(i['entrezgene']),
                    'taxid': str(i['taxid']),
                    'type_of_gene': i['type_of_gene'],
                    'gene_symbol': i['symbol'],
                    'protein_symbol': i['symbol'].upper(),
                    'name': i['name'],
                    'uniprot': uniprot,
                    'RSprotein': i['refseq']['protein'],
                    'genstart': str(i['genomic_pos']['start']),
                    'genstop': str(i['genomic_pos']['end']),
                    'strand': i['genomic_pos']['strand'],
                    'RSgenomic': i['genomic_pos']['chr'],
                    'strain': strain_qid,
                    'gene_description': gene_description,
                    'protein_description': protein_description,
                    'organism_name': self.organism,
                    'genus': self.genus,
                    'species': self.species,
                    'biological_process': '',
                    'cell_component': '',
                    'molecular_function': '',
                    'ec_number': ''
                }
                mgi_data.append(wd_data)
        return mgi_data

    def download_taxon_protein_GO(self):
        """
        Downloads the latest list of microbial proteins from uniprot, taxon specified by the strain takid provided.
        """

        url = 'http://www.uniprot.org/uniprot/'

        params = dict(query=('organism:' + self.strain_tid), format='tab',
                      columns='id,go(biological process),go(cellular component),go(molecular function),ec')
        r = requests.get(url=url, params=params)
        go_terms = r.text
        datareader = csv.reader(go_terms.splitlines(), delimiter="\t")
        uniprot_data = []

        for i in datareader:
            go_dict = {
                'uniprot': i[0],
                'biological_process': i[1], # biological process P682
                'cell_component': i[2], # cell component P681
                'molecular_function': i[3], # molecular function P680
                'ec_number': i[4]
            }
            uniprot_data.append(go_dict)
        return uniprot_data

    def combine_mgi_uniprot_dicts(self):
        mgi = self.gene_record
        unip = self.goterms
        all_data = []
        for m in mgi:
            for u in unip:
                if m['uniprot'] == u['uniprot']:
                    m.update(u)
            all_data.append(m)
        return all_data

class MicrobeResources2(object):

    def __init__(self, strain_data):
        self.strain_data = StrainDataParser(strain_data)
        self.gene_record = self.mygeneinfo_download()
        self.go_terms = self.download_taxon_protein_GO()
        self.combined = self.combine_mgi_uniprot_dicts()



class MyGeneInfoRestBatchQuery(object):
    def __init__(self, strain_data):
        self.strain_taxid = StrainDataParser(strain_data).strain_taxid
        self.gene_record = self.mygeneinfo_download()

    def mygeneinfo_download(self):
        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=self.strain_taxid, entrezonly="true", size="20", fields="all")
        r = requests.get(url=url, params=params)
        hits = r.json()
        strain_qid = WDProp2QID_SPARQL(prop='P685', string=self.strain_taxid).qid
        strain_label = WDQID2Label_SPARQL(qid=strain_qid).label
        gene_description = "microbial gene found in " + strain_label
        protein_description = "microbial protein found in " + strain_label

        mgi_data = []

        for i in hits['hits']:
            if i['type_of_gene'] != 'protein-coding':
                continue
            else:
                uniprot = ''
                if 'uniprot' in i.keys():
                    if 'Swiss-Prot' in i['uniprot']:
                        if isinstance(i['uniprot']['Swiss-Prot'],str):
                            uniprot = i['uniprot']['Swiss-Prot']
                        else:
                            uniprot = i['uniprot']['Swiss-Prot'][0]

                    if 'TrEMBL' in i['uniprot']:
                        if isinstance(i['uniprot']['TrEMBL'],str):
                            uniprot = i['uniprot']['TrEMBL']
                        else:
                            uniprot = i['uniprot']['TrEMBL'][0]
                else:
                    continue

                wd_data = {
                    '_geneid': str(i['entrezgene']),
                    'type_of_gene': i['type_of_gene'],
                    'gene_symbol': i['symbol'],
                    'protein_symbol': i['symbol'].upper(),
                    'name': i['name'],
                    'uniprot': uniprot,
                    'RSprotein': i['refseq']['protein'],
                    'genstart': str(i['genomic_pos']['start']),
                    'genstop': str(i['genomic_pos']['end']),
                    'strand': i['genomic_pos']['strand'],
                    'RSgenomic': i['genomic_pos']['chr'],
                    'gene_description': gene_description,
                    'protein_description': protein_description,
                    'biological_process': '',
                    'cell_component': '',
                    'molecular_function': '',
                    'ec_number': ''
                }
                mgi_data.append(wd_data)
        return mgi_data


class UniProtRESTBatchQuery(object):
    def __init__(self, strain_data):
        self.strain_taxid = StrainDataParser(strain_data).strain_taxid
        self.enzyme_record = self.download_taxon_protein_GO()
    def download_taxon_protein_GO(self):
        """
        Downloads the latest list of microbial proteins from uniprot, taxon specified by the strain takid provided.
        """

        url = 'http://www.uniprot.org/uniprot/'

        params = dict(query=('organism:' + self.strain_taxid), format='tab',
                      columns='id,go(biological process),go(cellular component),go(molecular function),ec')
        r = requests.get(url=url, params=params)
        go_terms = r.text
        datareader = csv.reader(go_terms.splitlines(), delimiter="\t")
        uniprot_data = []

        for i in datareader:
            go_dict = {
                'uniprot': i[0],
                'biological_process': i[1], # biological process P682
                'cell_component': i[2], # cell component P681
                'molecular_function': i[3], # molecular function P680
                'ec_number': i[4]
            }
            uniprot_data.append(go_dict)
        return uniprot_data


class StrainDataParser(object):
    def __init__(self,strain_data):
        self.strain_data = strain_data
        self.species_taxid = str(self.strain_data[0])
        self.strain_taxid = self.strain_data[1]
        self.taxon_name = " ".join(self.strain_data[2:])
        self.genus = self.strain_data[2]
        self.species = self.strain_data[3]
        self.strain = self.strain_data[4]


class GeneDataParser(object):
    def __init__(self, gene_data):
        self.gene_data = gene_data
        self.RS_genome = self.gene_data['RSgenomic']
        self.strand = str(self.gene_data['strand'])
        self.gene_description =self.gene_data['gene_description']
        self.type_of_gene = self.gene_data['type_of_gene']
        self.name = self.gene_data['name']
        self.gene_symbol = self.gene_data['gene_symbol']
        self.geneid = str(self.gene_data['_geneid'])
        self.genstop = str(self.gene_data['genstop'])
        self.genstart = str(self.gene_data['genstart'])
        self.protein_description = self.gene_data['protein_description']
        self.protein_symbol = self.gene_data['protein_symbol']
        self.RS_protein = self.gene_data['RSprotein']
        self.uniprotid = self.gene_data['uniprot']
        self.GO_BP = self.gene_data['biological_process']
        self.GO_MF = self.gene_data['molecular_function']
        self.GO_CC = self.gene_data['cell_component']
        self.ec_number = str(self.gene_data['ec_number'])


class MGI_UNIP_Merger(object):
    def __init__(self, mgi, unip):
        self.mgi_data = mgi
        self.unip_data = unip
        self.mgi_unip_dict = self.combine_mgi_uniprot_dicts()

    def combine_mgi_uniprot_dicts(self):
        all_data = []
        for m in self.mgi_data:
            for u in self.unip_data:
                if m['uniprot'] == u['uniprot']:
                    m.update(u)
            all_data.append(m)
        return all_data







        '''
        self.RS_genome = self.gene_data['RSgenomic']
        self.strand = str(self.gene_data['strand'])
        self.gene_description =self.gene_data['gene_description']
        self.type_of_gene = self.gene_data['type_of_gene']
        self.name = self.gene_data['name']
        self.gene_symbol = self.gene_data['gene_symbol']
        self.geneid = str(self.gene_data['_geneid'])
        self.genstop = str(self.gene_data['genstop'])
        self.genstart = str(self.gene_data['genstart'])
        self.protein_description = self.gene_data['protein_description']
        self.protein_symbol = self.gene_data['protein_symbol']
        self.RS_protein = self.gene_data['RSprotein']
        self.uniprotid = self.gene_data['uniprot']
        self.GO_BP = self.gene_data['biological_process']
        self.GO_MF = self.gene_data['molecular_function']
        self.GO_CC = self.gene_data['cell_component']
        self.ec_number = str(self.gene_data['ec_number'])
        '''


class GeneticEntityInstanceParser(object):

    def __init__(self, strain_data):
        '''
        #input: dictionary in list of dicts from resource collection
        #parse the contents of the dictionary for each gene entry for use with different bots
        '''
        self.strain_data = strain_data

        self.organism_name = self.strain_data['organism_name']
        self.genus = self.strain_data['genus']
        self.species = self.strain_data['species']
        self.strain = self.strain_data['strain']

        self.species_taxid = str(self.strain_data['species_taxid'])
        self.strain_tid = self.strain_data['strain_taxid']

        self.RS_genome = self.strain_data['RSgenomic']
        self.strand = str(self.strain_data['strand'])

        self.gene_description =self.strain_data['gene_description']
        self.type_of_gene = self.strain_data['type_of_gene']

        self.name = self.strain_data['name']
        self.gene_symbol = self.strain_data['gene_symbol']

        self.geneid = str(self.strain_data['_geneid'])

        self.genstop = str(self.strain_data['genstop'])
        self.genstart = str(self.strain_data['genstart'])

        self.protein_description = self.strain_data['protein_description']
        self.protein_symbol = self.strain_data['protein_symbol']
        self.RS_protein = self.strain_data['RSprotein']
        self.uniprotid = self.strain_data['uniprot']

        self.GO_BP = self.strain_data['biological_process']
        self.GO_MF = self.strain_data['molecular_function']
        self.GO_CC = self.strain_data['cell_component']
        self.ec_number = str(self.strain_data['ec_number'])






'''

class TaxBot(object):

    def __init__(self, strain_data):

        #Call while iterating through master list of reference genome data (tid_list).
        #:param ref_org: reference strain genome data list from master list
        #ex. ['9', '107806', 'Buchnera', 'aphidicola', 'str. APS (Acyrthosiphon pisum)']
        #:return: Finds appropriate strain item or creates it.

        self.strain_data = GeneticEntityInstanceParser(strain_data)
        self.strain_item_data = []

    def strain_item_construction(self):

        parent_data = [PBB_Core.WDString(value=self.species_tid, prop_nr='P685')]
        parent_item = PBB_Core.WDItemEngine(item_name=self.gen_spec, domain='genomes', data=parent_data)

        self.strain_item_data.append(PBB_Core.WDItemID(value=parent_item.wd_item_id, prop_nr='P171')) # Parent QID
        self.strain_item_data.append(PBB_Core.WDString(value=self.strain_tid, prop_nr='P685')) # Tax id
        self.strain_item_data.append(PBB_Core.WDString(value=self.organism, prop_nr='P225')) # Taxon name
        self.strain_item_data.append(PBB_Core.WDItemID(value='Q855769', prop_nr='P105')) #Taxon Rank strain

        wd_item = PBB_Core.WDItemEngine(item_name=self.organism, domain='genomes', data=self.strain_item_data)
        wd_item.set_aliases([self.strain])
        wd_item.set_description('bacterial strain')
        pprint.pprint(wd_item.get_wd_json_representation())
        #wd_item.write(login)


class MicrobeGeneBot(object):
    def __init__(self):






a = NCBIReferenceGenomes()
for i in a.tid_list:
    b = MicrobeResources(i)

    strain_genetic_data = b.combined
    for h in strain_genetic_data:
        try:
            print(len(h['biological_process']))
        except:
            print(i, h, "this is the bad one that nobody likes")




    def write_gene_item(self):
        """
        Write gene items using dictionary from wd_parse_mgi(self):
        :return:
        """
        zwd_write_data = self.dbdata
        count = 0
        for i in zwd_write_data:
            wd_write_data = ast.literal_eval(i)

            if '_geneid' not in wd_write_data.keys():
                continue
            else:

                alias_list = [wd_write_data['gene_symbol']]
                item_name = wd_write_data['name'] + "  " + wd_write_data['gene_symbol']
                description = wd_write_data['gene_description']

                NCBIgenerefStated = PBB_Core.WDItemID(value='Q20641742', prop_nr='P248', is_reference=True)
                NCBIgenerefStated.overwrite_references = True
                timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
                refRetrieved.overwrite_references = True
                uniprot_protein_reference = [NCBIgenerefStated, refRetrieved]




                statements = dict()
                statements['found_in'] = [PBB_Core.WDItemID(value=wd_write_data['strain'], prop_nr='P703', references=[copy.deepcopy(uniprot_protein_reference)])] #Found in taxon
                statements['geneid'] = [PBB_Core.WDString(value=wd_write_data['_geneid'], prop_nr='P351', references=[copy.deepcopy(uniprot_protein_reference)])]
                statements['subclass'] = [PBB_Core.WDItemID(value='Q7187', prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)])]
                statements['genomic_start'] = [PBB_Core.WDString(value=wd_write_data['genstart'], prop_nr='P644', references=[copy.deepcopy(uniprot_protein_reference)])]
                statements['genomic_stop'] = [PBB_Core.WDString(value=wd_write_data['genstop'], prop_nr='P645', references=[copy.deepcopy(uniprot_protein_reference)])]


                try:
                    gene_product = WDProp2QID_SPARQL(prop='P637', string=wd_write_data['RSprotein'])
                    gene_product = gene_product.qid
                    if gene_product == 'none':
                        pass
                    else:
                        statements['encodes'] = [PBB_Core.WDItemID(value=gene_product, prop_nr='P688', references=[copy.deepcopy(uniprot_protein_reference)])]

                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='No protein item found {}'.format(wd_write_data['_geneid']))

                final_statements = []

                for key in statements.keys():

                    for statement in statements[key]:
                        final_statements.append(statement)

                try:
                    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=final_statements)
                    PBB_Core.WDItemEngine.log(level='INFO', message='Gene item found {}'.format(wd_write_data['_geneid'] + " " + str(count) ))

                except Exception as e:

                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item data discrepency {}'.format(wd_write_data['name']))



                try:

                    wd_item_gene.set_label(item_name)
                    wd_item_gene.set_description(description)
                    wd_item_gene.set_aliases(alias_list)
                    pprint.pprint(wd_item_gene.get_wd_json_representation())
                    wd_item_gene.write(login)
                    count += 1
                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item {} written successfully'.format(wd_write_data['name']))
                    print('{} gene items written'.format(count))
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item write failed {}'.format(wd_write_data['name']))
                    continue





'''


a = NCBIReferenceGenomes()
for i in a.tid_list:
    mgi_record = MyGeneInfoRestBatchQuery(i).gene_record
    unip_record = UniProtRESTBatchQuery(i).enzyme_record
    combined = MGI_UNIP_Merger(mgi=mgi_record, unip=unip_record)
    print(combined.mgi_unip_dict)








