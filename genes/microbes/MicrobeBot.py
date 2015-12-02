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

if len(sys.argv) < 5:
    print("   You did not supply the proper arguments!")
    print("   Usage: MicrobeBot.py <Wikidata user name> <Wikidata Password> <Path of source files> <domain i.e. genes/proteins")
    sys.exit()
else:
    pass


next7 =[['287', '208964', 'Pseudomonas aeruginosa PAO1', 'PAO1'], ['303', '160488', 'Pseudomonas putida KT2440', 'KT2440'],['197', '192222', 'Campylobacter jejuni subsp. jejuni NCTC 11168 = ATCC 700819', 'subsp. jejuni NCTC 11168 = ATCC 700819'], ['210', '85962', 'Helicobacter pylori 26695', '26695'], ['263', '177416', 'Francisella tularensis subsp. tularensis SCHU S4', 'subsp. tularensis SCHU S4'], ['274', '300852', 'Thermus thermophilus HB8', 'HB8']]

login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
source_path = sys.argv[3] #"/Users/timputman/working_repos/Sources/"
file_list = os.listdir(source_path)

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
            final_qid.append('none')
        return final_qid[0]


class WDLabel2QID(object): # This is where i left off...current label finder is not specific
    def __init__(self,label=''):
        self.qid = self.get_items_qid_by_label(label)

    def get_items_qid_by_label(self, label):

        url = 'https://{}/w/api.php'.format("www.wikidata.org")
        params = {
            'action': 'wbsearchentities',
            'language': 'en',
            'search': label,
            'format': 'json'
        }
        qidout = []
        try:
            reply = requests.get(url, params=params)
            replyjson = reply.json()
            return replyjson
            #qidout.append(replyjson['search'][0]['id'])
        except:
            qidout.append('None')

        #return qidout[0]


class WDQID2Label(object):
    def __init__(self, qid=''):
        """
        Gets all WikiData item label using qid
        :param wdquery: A string representation of a WD query
        :return: A Python json representation object with the search results is returned
        """
        self.qid = qid
        self.label = self.get_items_label_by_QID(qid)

    def get_items_label_by_QID(self, qid):
        url = 'https://www.wikidata.org/w/api.php/'
        param = dict(action='wbgetentities', props='labels', ids=qid, format='json')
        reply = requests.get(url, params=param)
        resp = reply.json()
        out = []
        try:
            eng_label = resp['entities'][qid]['labels']['en']['value']
            out.append(eng_label)
        except:
            out.append('None')
        return out[0]


class WDProp2QID(object):
    def __init__(self, string='', prop=''):
        """
        Gets all WikiData item IDs that contains statements containing property 'prop' (integer omitting the p)
        with value 'string'
        :param wdquery: A string representation of a WD query
        :return: A Python json representation object with the search results is returned
        """
        self.string = string
        self.prop = prop
        self.qid = self.get_items_QID_by_property(string,prop)

    def get_items_QID_by_property(self, string, prop):
        url = 'http://wdq.wmflabs.org/api'
        wdquery = "string[{}:\"{}\"]".format(prop, string)
        reply = requests.get(url, params={'q': wdquery})
        a = reply.json()
        out = []
        try:
            qidout = "Q" + str(a['items'][0])
            out.append(qidout)
        except:
            out.append("None")
        return str(out[0])


class NCBIReferenceGenomoes(object):
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

        all_strain_data = []
        for row in datareader:
            org = row[7].split()
            strain = " ".join(org[2:])
            if row[4] == 'reference genome':
                strain_data = [row[6], row[5], row[7], strain]
                all_strain_data.append(strain_data)
        return all_strain_data


class WDStrainItem(object):
    def __init__(self, ref_orgs):

        self.ref_orgs = ref_orgs

    def wd_species_items(self):
        species = list(self.ref_orgs)
        description = "species of prokaryote"

        for i in species:
            data = list()
            species_all = i[2].split(" ")
            species = " ".join(species_all[0:2])
            item_name = species
            alias = [i[-1]]
            spec_tid = str(i[0])
            data.append(PBB_Core.WDString(value=spec_tid, prop_nr='P685')) # Species taxid
            data.append(PBB_Core.WDString(value=species, prop_nr='P225')) # Taxon name
            data.append(PBB_Core.WDItemID(value='Q7432', prop_nr='P105')) #Taxon Rank species
            wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=data)
            wd_item.set_aliases(alias)
            wd_item.set_description(description)
            pprint.pprint(wd_item.get_wd_json_representation())
            wd_item.write(login)

    def wd_strain_genome_items(self):
        """
        Generate item for each bacterial strain in wikidata
        :return:
        """
        genomes = list(self.ref_orgs)

        description = "bacterial strain"

        for i in genomes:

            try:
                data = list()
                item_name = i[2]
                alias = [i[-1]]
                spec_tid = str(i[0])
                parent_qid = WDProp2QID_SPARQL(prop='P685',string=spec_tid)
                data.append(PBB_Core.WDItemID(value=parent_qid.qid, prop_nr='P171')) # Parent QID
                tid = str(i[1])
                data.append(PBB_Core.WDString(value=tid, prop_nr='P685')) # Tax id
                data.append(PBB_Core.WDString(value=i[2], prop_nr='P225')) # Taxon name
                data.append(PBB_Core.WDItemID(value='Q855769', prop_nr='P105')) #Taxon Rank strain
                wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=data)
                wd_item.set_aliases(alias)
                wd_item.set_description(description)
                pprint.pprint(wd_item.get_wd_json_representation())
                wd_item.write(login)

            except IndexError:
                print("{} didn't have a parent".format(i[2]))
                continue


class WDGeneProteinItemDownload(object):
    def __init__(self, ref_orgs):
        self.ref_orgs = ref_orgs
        self.spec_taxid = self.ref_orgs[0]
        self.strain_taxid = self.ref_orgs[1]
        self.taxname = self.ref_orgs[2]
        self.strain = self.ref_orgs[3]
        self.gene_record = self.gain_refseq_mgi()
        self.goterms = self.download_taxon_protein_GO()
        self.combo_mu = self.combine_mgi_uniprot_dicts()

    def gain_refseq_mgi(self):
        """
        Query mygene.info by tax id.  Return all gene records for every taxid entered in json
        :return:
        """

        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=self.strain_taxid, entrezonly="true", size="10000", fields="all")
        r = requests.get(url, params)

        hits = r.json()

        mgi_data = []

        for i in hits['hits']:
            if i['type_of_gene'] != 'protein-coding':
                continue


            else:
                name = i['name'] #+ " " + i['symbol']
                try:
                    uniprot = i['uniprot']['Swiss-Prot']
                except Exception:
                    try:
                        uniprot = i['uniprot']['TrEMBL']
                    except Exception:
                        continue

                taxid = str(i['taxid'])
                strain = WDProp2QID_SPARQL(prop='P685',string=taxid)
                strain = strain.qid
                q2label = WDQID2Label(strain)
                gene_description = "microbial gene found in " + q2label.label
                protein_description = "microbial protein found in " + q2label.label
                wd_data = {
                    '_geneid': str(i['entrezgene']),
                    'taxid': str(i['taxid']),
                    'type_of_gene': i['type_of_gene'],
                    'gene_symbol': i['symbol'],
                    'protein_symbol': i['symbol'].upper(),
                    'name': name,
                    'uniprot': uniprot,
                    'RSprotein': i['refseq']['protein'],
                    'genstart': str(i['genomic_pos']['start']),
                    'genstop': str(i['genomic_pos']['end']),
                    'strand': i['genomic_pos']['strand'],
                    'RSgenomic': i['genomic_pos']['chr'],
                    'strain': strain,
                    'gene_description': gene_description,
                    'protein_description': protein_description
                }
                mgi_data.append(wd_data)
        return mgi_data

    def download_taxon_protein_GO(self):
        """
        Downloads the latest list of human proteins from uniprot through the URL specified in mygene_info_settings
        """

        url = 'http://www.uniprot.org/uniprot/'

        params = dict(query=('organism:' + self.strain_taxid), format='tab', columns='id,go(biological process),go(cellular component),go(molecular function)')
        r = requests.get(url, params=params)
        go_terms = r.text
        datareader = csv.reader(go_terms.splitlines(), delimiter="\t")
        uniprot_data = []

        for i in datareader:
            go_dict = {
                'uniprot': i[0],
                'biological_process': i[1], # biological process P682
                'cell_component': i[2], # cell component P681
                'molecular_function': i[3] # molecular function P680
            }
            uniprot_data.append(go_dict)
        return uniprot_data

    def combine_mgi_uniprot_dicts(self):
        mgi = self.gene_record
        unip = self.goterms
        out = open(source_path+'10_test_mgi_uniprot_combined_{}_{}.dict'.format(time.time(), self.taxname +"\t"+ str(self.strain_taxid)), "w")

        for m in mgi:
            for u in unip:
                if m['uniprot'] == u['uniprot']:
                    m.update(u)

            print(m, file=out)


class WDWriteGeneProteinItems(object):
    def __init__(self, infile=''):
        self.dbdata = open(infile, "r")

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



    def write_protein_item(self):
        """
        Write protein items using dictionary from wd_parse_mgi(self):
        :return:
        """
        zwd_write_data = self.dbdata
        count = 0
        for i in zwd_write_data:

            wd_write_data = ast.literal_eval(i)
            count += 1

            if '_geneid' not in wd_write_data.keys():
                continue
            else:
                item_name = wd_write_data['name'] + " " + wd_write_data['protein_symbol']
                description = wd_write_data['protein_description']
                alias_list = [wd_write_data['protein_symbol']]

                statements = dict()

                uniprotrefStated = PBB_Core.WDItemID(value='Q905695', prop_nr='P248', is_reference=True)
                uniprotrefStated.overwrite_references = True
                timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
                refRetrieved.overwrite_references = True
                uniprot_protein_reference = [uniprotrefStated, refRetrieved]

                try:
                    gene_item = WDProp2QID_SPARQL(prop='P351',string=wd_write_data['_geneid']).qid
                    gene_item = gene_item
                    if gene_item is not 'None':
                        statements['encodedby'] = [PBB_Core.WDItemID(value=gene_item, prop_nr='P702', references=[copy.deepcopy(uniprot_protein_reference)])]
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='No gene item found {}'.format(e))




                statements['found_in'] = [PBB_Core.WDItemID(value=wd_write_data['strain'], prop_nr='P703', references=[copy.deepcopy(uniprot_protein_reference)])] #Found in taxon
                statements['uniprot'] = [PBB_Core.WDString(value=wd_write_data['uniprot'], prop_nr='P352', references=[copy.deepcopy(uniprot_protein_reference)])]
                statements['proteinid'] = [PBB_Core.WDString(value=wd_write_data['RSprotein'],prop_nr='P637', references=[copy.deepcopy(uniprot_protein_reference)])]
                #statements['instance'] = [PBB_Core.WDItemID(value='Q8054', prop_nr='P31', references=uniprot_protein_reference)]
                statements['subclass'] = [PBB_Core.WDItemID(value='Q8054', prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)])]
                statements['molecular_function'] = []
                statements['cell_component'] = []
                statements['biological_process'] = []


                mfcount = 0
                if wd_write_data['molecular_function']:
                    mflist = wd_write_data["molecular_function"].split(";")  # P680
                    mfdictlist = []

                    for g in mflist:
                        mfsplitlist = dict()
                        mf = g.split()
                        mfsplitlist['mfgid']=mf[-1][4:-1]
                        mfsplitlist['mfgterm']=" ".join(mf[:-1])
                        mfdictlist.append(mfsplitlist)

                        mfgoqid = WDProp2QID_SPARQL(prop='P686',string=mfsplitlist['mfgid']).qid
                        mfgolabel = WDQID2Label(qid=mfgoqid)
                        goqid =[]

                        if mfsplitlist['mfgterm'] == mfgolabel.label:
                            goqid.append(mfgoqid)
                        else:
                            pass

                        if mfgoqid == 'None':
                            properties = list()
                            properties.append(PBB_Core.WDString(value=mfsplitlist['mfgid'], prop_nr='P686', references=[copy.deepcopy(uniprot_protein_reference)]))
                            properties.append(PBB_Core.WDItemID(value='Q14860489', prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)]))
                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=mfsplitlist['mfgterm'], data=properties,
                                                                 domain="proteins")
                                goWdPage.set_label(mfsplitlist['mfgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([mf[-1][1:-1]])
                                #pprint.pprint(goWdPage.get_wd_json_representation())

                                goWdPage.write(login)
                                mfcount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(mfsplitlist['mfgterm'] + str(mfcount)))

                                print('MF GO Item written {}'.format(mfcount))
                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO', message='failure to write new go term item {}'.format(e))

                        else:
                            try:
                                statements['molecular_function'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P680', references=[copy.deepcopy(uniprot_protein_reference)]))
                            except Exception:
                                pass

                cccount = 0
                if wd_write_data['cell_component']:
                    cclist = wd_write_data['cell_component'].split(";")  # P681
                    ccdictlist = []

                    for g in cclist:
                        ccsplitlist = dict()
                        cc = g.split()
                        ccsplitlist['ccgid'] = cc[-1][4:-1]
                        ccsplitlist['ccgterm'] = " ".join(cc[:-1])
                        ccdictlist.append(ccsplitlist)

                        ccgoqid = WDProp2QID_SPARQL(prop='P686',string=ccsplitlist['ccgid']).qid
                        ccgolabel = WDQID2Label(qid=ccgoqid)
                        goqid =[]
                        if ccsplitlist['ccgterm'] == ccgolabel.label:
                            goqid.append(ccgoqid)
                        else:
                            pass


                        if ccgoqid == 'None':

                            properties = list()
                            properties.append(PBB_Core.WDString(value=ccsplitlist['ccgid'],
                                              prop_nr='P686', references=[copy.deepcopy(uniprot_protein_reference)]))
                            properties.append(PBB_Core.WDItemID(value='Q5058355',
                                               prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)]))

                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=ccsplitlist['ccgterm'], data=properties,
                                                                 domain="proteins")
                                goWdPage.set_label(ccsplitlist['ccgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([cc[-1][1:-1]])

                                goWdPage.write(login)
                                cccount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(ccsplitlist['ccgterm'] + str(ccount)))
                                print('CC GO Item written {}'.format(cccount))
                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO',
                                                          message='failure to write new go term item {}'.format(e))
                        else:
                            try:
                                statements['cell_component'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P681',
                                                                                   references=[copy.deepcopy(uniprot_protein_reference)]))
                            except Exception:
                                pass

                bpcount = 0
                if wd_write_data['biological_process']:
                    bplist = wd_write_data['biological_process'].split(";")  # P682
                    bpdictlist = []

                    for g in bplist:
                        bpsplitlist = dict()
                        bp = g.split()
                        bpsplitlist['bpgid'] = bp[-1][4:-1]
                        bpsplitlist['bpgterm'] = " ".join(bp[:-1])
                        bpdictlist.append(bpsplitlist)

                        bpgoqid = WDProp2QID_SPARQL(prop='P686', string=bpsplitlist['bpgid']).qid
                        bpgolabel = WDQID2Label(qid=bpgoqid)
                        goqid =[]
                        if bpsplitlist['bpgterm'] == bpgolabel.label:
                            goqid.append(bpgoqid)
                        else:
                            pass

                        if bpgoqid == 'None':
                            properties = list()
                            properties.append(PBB_Core.WDString(value=bpsplitlist['bpgid'],
                                              prop_nr='P686', references=[copy.deepcopy(uniprot_protein_reference)]))
                            properties.append(PBB_Core.WDItemID(value='Q2996394',
                                               prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)]))

                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=bpsplitlist['bpgterm'], data=properties,
                                                                 domain="proteins")
                                goWdPage.set_label(bpsplitlist['bpgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([bp[-1][1:-1]])

                                goWdPage.write(login)
                                bpcount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(bpsplitlist['bpgterm'] + str(bpcount)))
                                print('BP GO Item written {}'.format(bpcount))

                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO',
                                                          message='failure to write new go term item {}'.format(e))

                        else:
                            try:
                                statements['biological_process'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P682',
                                                                                          references=[copy.deepcopy(uniprot_protein_reference)]))

                            except Exception:
                                pass



                final_statements = []

                for key in statements.keys():
                    for statement in statements[key]:
                        final_statements.append(statement)
                        #print(key, statement.prop_nr, statement.value)



                try:
                    wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='proteins', data=final_statements)
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item {}'.format(wd_write_data['name']))

                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item data discrepency {}'.format(wd_write_data['name']))

                try:
                    wd_item_protein.set_label(item_name)
                    wd_item_protein.set_description(description)
                    wd_item_protein.set_aliases(alias_list)
                    #pprint.pprint(wd_item_protein.get_wd_json_representation())
                    wd_item_protein.write(login)
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item {} written successfully'.format(wd_write_data['name'] + " " + str(count)))
                    print('{} protein items written'.format(count))
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='Protein error {}'.format(e))
                    continue


####Call section####

#####Get current Reference Genome List from NCBI
genomes = NCBIReferenceGenomoes()
strain_data = genomes.tid_list


#####Use strain data to download gene and protein data from Mygene.info and Uniprot
#####Generates files of data for each strain with a dictionary for each gene
for i in next7: #use strain_data for a full run


    genetic_data = WDGeneProteinItemDownload(i)
    genetic_data.combo_mu


#####Step through gene data files in current directory and feed them to the WDWriteGeneProteinItems()



for i in file_list:
    if '10_test' in i:
        a = WDWriteGeneProteinItems(infile=source_path+i)
        if sys.argv[4] == 'genes':
            a.write_gene_item()
        if sys.argv[4] =='proteins':
            a.write_protein_item()
