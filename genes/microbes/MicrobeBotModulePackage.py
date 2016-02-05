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
from time import gmtime, strftime
import time
import copy

__author__ = 'timputman'



if len(sys.argv) < 5:
    print("   You did not supply the proper arguments!")
    print("   Usage: MicrobeBotModularPackage.py <Wikidata user name> <Wikidata Password> <domain i.e. genes/proteins/encode_genes/encode_proteins> <microbial strain taxid>")
    sys.exit()
else:
    pass

class ReferenceStore(object):
    def _init_(self):
        self.R_uniprot = self.uniprot_ref()

    def uniprot_ref(self):
        uniprotrefStated = PBB_Core.WDItemID(value='Q905695', prop_nr='P248', is_reference=True)
        uniprotrefStated.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        return [uniprotrefStated, refRetrieved]


    def ncbi_ref(self):
        NCBIgenerefStated = PBB_Core.WDItemID(value='Q20641742', prop_nr='P248', is_reference=True)
        NCBIgenerefStated.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        return [NCBIgenerefStated, refRetrieved]


class WDProp2QIDSPARQL(object):
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


class WDQID2LabelSPARQL(object):
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
        self.locus_tag = self.gene_data['locus_tag']
        self.RS_genome = self.gene_data['RSgenomic']
        self.strand = str(self.gene_data['strand'])
        self.type_of_gene = self.gene_data['type_of_gene']
        self.name = self.gene_data['name']
        self.gene_symbol = self.gene_data['gene_symbol']
        self.geneid = str(self.gene_data['_geneid'])
        self.genstop = str(self.gene_data['genstop'])
        self.genstart = str(self.gene_data['genstart'])
        self.protein_symbol = self.gene_data['protein_symbol']
        self.RS_protein = self.gene_data['RSprotein']
        self.uniprotid = self.gene_data['uniprot']
        self.GO_BP = self.gene_data['biological_process']
        self.GO_MF = self.gene_data['molecular_function']
        self.GO_CC = self.gene_data['cell_component']
        self.ec_number = self.gene_data['ec_number']


class MyGeneInfoRestBatchQuery(object):
    def __init__(self, strain_data):
        self.strain_taxid = StrainDataParser(strain_data).strain_taxid
        self.gene_record = self.mygeneinfo_download()

    def mygeneinfo_download(self):
        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=self.strain_taxid, entrezonly="true", size="10000", fields="all")
        r = requests.get(url=url, params=params)
        hits = r.json()

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
                      columns='id,go(biological process),go(cellular component),go(molecular function),ec,genes(OLN)')
        r = requests.get(url=url, params=params)
        go_terms = r.text
        datareader = csv.reader(go_terms.splitlines(), delimiter="\t")
        next(datareader, None)
        uniprot_data = []

        for i in datareader:
            go_dict = dict()
            go_dict['uniprot'] = i[0]
            go_dict['locus_tag'] = i[5]

            if i[4]:
                eclist = i[4].split(";")
                go_dict['ec_number'] = eclist

            if i[1]:
                bplist = i[1].split(";")  # P680
                bpgolist= []
                for item in bplist:
                    bpdict = {}
                    bp = item.split()
                    bpdict['bp_goid'] = bp[-1][1:-1]
                    bpdict['bp_goterm'] = " ".join(bp[:-1])
                    bpgolist.append(bpdict)
                go_dict['biological_process'] = bpgolist

            if i[2]:
                cclist = i[2].split(";")  # P680
                ccgolist= []
                for item in cclist:
                    ccdict = {}
                    cc = item.split()
                    ccdict['cc_goid'] = cc[-1][1:-1]
                    ccdict['cc_goterm'] = " ".join(cc[:-1])
                    ccgolist.append(ccdict)
                go_dict['cell_component'] = ccgolist

            if i[3]:
                mflist = i[3].split(";")  # P680
                mfgolist= []
                for item in mflist:
                    mfdict = {}
                    mf = item.split()
                    mfdict['mf_goid'] = mf[-1][1:-1]
                    mfdict['mf_goterm'] = " ".join(mf[:-1])
                    mfgolist.append(mfdict)
                go_dict['molecular_function'] = mfgolist

            uniprot_data.append(go_dict)
        return uniprot_data


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


class WDGeneItem(object):
    def __init__(self, gene_record, strain_record):
        self.gene_record = GeneDataParser(gene_record)
        self.strain_record = StrainDataParser(strain_record)


    def gene_item(self):
        """
        Write gene items using dictionary from wd_parse_mgi(self):
        :return:
        """
        item_name = self.gene_record.name + "\t" + self.gene_record.gene_symbol
        alias_list = [self.gene_record.gene_symbol]
        strain_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.strain_taxid).qid
        strain_label = WDQID2LabelSPARQL(qid=strain_qid).label
        description = "microbial gene found in " + strain_label

        NCBIgenerefStated = PBB_Core.WDItemID(value='Q20641742', prop_nr='P248', is_reference=True)
        NCBIgenerefStated.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        NCIB_gene_reference = [NCBIgenerefStated, refRetrieved]

        statements = list()
        statements.append(PBB_Core.WDItemID(value=strain_qid, prop_nr='P703', references=[copy.deepcopy(NCIB_gene_reference)])) #Found in taxon
        statements.append(PBB_Core.WDString(value=self.gene_record.geneid, prop_nr='P351', references=[copy.deepcopy(NCIB_gene_reference)]))
        statements.append(PBB_Core.WDString(value=self.gene_record.locus_tag, prop_nr='P2393', references=[copy.deepcopy(NCIB_gene_reference)]))
        statements.append(PBB_Core.WDItemID(value='Q7187', prop_nr='P279', references=[copy.deepcopy(NCIB_gene_reference)]))
        statements.append(PBB_Core.WDString(value=self.gene_record.genstart, prop_nr='P644', references=[copy.deepcopy(NCIB_gene_reference)]))
        statements.append(PBB_Core.WDString(value=self.gene_record.genstop, prop_nr='P645', references=[copy.deepcopy(NCIB_gene_reference)]))

        start = time.time()

        try:
            wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=statements, use_sparql=True)
            wd_item_gene.set_label(item_name)
            wd_item_gene.set_description(description)
            wd_item_gene.set_aliases(alias_list)
            #pprint.pprint(wd_item_gene.get_wd_json_representation())
            wd_item_gene.write(login)

            new_mgs = ''
            if wd_item_gene.create_new_item:
                new_mgs = ': New item'
            else:
                new_mgs = ': Eddited_item'
            PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                main_data_id=self.gene_record.geneid,
                exception_type='',
                message='success{}'.format(new_mgs),
                wd_id=wd_item_gene.wd_item_id,
                duration=time.time() - start
                ))

            print('success')

        except Exception as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=self.gene_record.geneid,
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))

        end = time.time()
        print('Time elapsed:', end - start)


class WDProteinItem(object):
    def __init__(self, gene_record, strain_record):
        self.gene_record = GeneDataParser(gene_record)
        self.strain_record = StrainDataParser(strain_record)
        self.final_protein_statements = []

    def protein_item(self):

        item_name = self.gene_record.name + "\t" + self.gene_record.protein_symbol
        alias_list = [self.gene_record.protein_symbol]
        strain_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.strain_taxid).qid
        strain_label = WDQID2LabelSPARQL(qid=strain_qid).label
        description = "microbial protein found in " + strain_label

        uniprotrefStated = PBB_Core.WDItemID(value='Q905695', prop_nr='P248', is_reference=True)
        uniprotrefStated.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        uniprot_protein_reference = [uniprotrefStated, refRetrieved]

        statements = {}
        statements['found_in'] = [PBB_Core.WDItemID(value=strain_qid, prop_nr='P703', references=[copy.deepcopy(uniprot_protein_reference)])] #Found in taxon
        statements['uniprot'] = [PBB_Core.WDString(value=self.gene_record.uniprotid, prop_nr='P352', references=[copy.deepcopy(uniprot_protein_reference)])]
        statements['proteinid'] = [PBB_Core.WDString(value=self.gene_record.RS_protein, prop_nr='P637', references=[copy.deepcopy(uniprot_protein_reference)])]
        statements['subclass'] = [PBB_Core.WDItemID(value='Q8054', prop_nr='P279', references=[copy.deepcopy(uniprot_protein_reference)])]
        statements['molecular_function'] = []
        statements['cell_component'] = []
        statements['biological_process'] = []
        statements['ec_number'] = []

        if self.gene_record.ec_number:
            for i in self.gene_record.ec_number:
                statements['ec_number'].append(PBB_Core.WDString(value=i, prop_nr='P591', references=[copy.deepcopy(uniprot_protein_reference)]))

        mfgoqidlist = []
        if self.gene_record.GO_MF:
            mfdict = {}
            for mfgt in self.gene_record.GO_MF:
                mfdict['go_qid'] = WDProp2QIDSPARQL(prop='P686', string= mfgt['mf_goid']).qid
                mfdict['go_label'] = WDQID2LabelSPARQL(qid=mfdict['go_qid']).label
                if mfgt['mf_goterm'] == mfdict['go_label']:
                    mfgoqidlist.append(mfdict['go_qid'])
            if mfgoqidlist:
                for i in mfgoqidlist:
                    statements['molecular_function'].append(PBB_Core.WDItemID(value=i, prop_nr='P680', references=[copy.deepcopy(uniprot_protein_reference)]))

        ccgoqidlist = []
        if self.gene_record.GO_CC:
            ccdict = {}
            for ccgt in self.gene_record.GO_CC:
                ccdict['go_qid'] = WDProp2QIDSPARQL(prop='P686', string= ccgt['cc_goid']).qid
                ccdict['go_label'] = WDQID2LabelSPARQL(qid=ccdict['go_qid']).label
                if ccgt['cc_goterm'] == ccdict['go_label']:
                    ccgoqidlist.append(ccdict['go_qid'])
            if ccgoqidlist:
                for i in ccgoqidlist:
                    statements['cell_component'].append(PBB_Core.WDItemID(value=i, prop_nr='P681', references=[copy.deepcopy(uniprot_protein_reference)]))

        bpgoqidlist = []
        if self.gene_record.GO_BP:
            bpdict = {}
            for bpgt in self.gene_record.GO_BP:
                bpdict['go_qid'] = WDProp2QIDSPARQL(prop='P686', string= bpgt['bp_goid']).qid
                bpdict['go_label'] = WDQID2LabelSPARQL(qid=bpdict['go_qid']).label
                if bpgt['bp_goterm'] == bpdict['go_label']:
                    bpgoqidlist.append(bpdict['go_qid'])
            if bpgoqidlist:
                for i in bpgoqidlist:
                    statements['biological_process'].append(PBB_Core.WDItemID(value=i, prop_nr='P682', references=[copy.deepcopy(uniprot_protein_reference)]))

        for key in statements.keys():
            for statement in statements[key]:
                self.final_protein_statements.append(statement)

        start = time.time()

        try:
            wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='proteins', data=self.final_protein_statements, use_sparql=True)
            wd_item_protein.set_label(item_name)
            wd_item_protein.set_description(description)
            wd_item_protein.set_aliases(alias_list)
            #pprint.pprint(wd_item_protein.get_wd_json_representation())
            #pprint.pprint(self.gene_record.gene_data)
            wd_item_protein.write(login)

            new_mgs = []
            if wd_item_protein.create_new_item:
                new_mgs.append(': New item')
            else:
                new_mgs.append(': Eddited_item')

            PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                main_data_id=self.gene_record.RS_protein,
                exception_type='',
                message='success{}'.format(new_mgs),
                wd_id=wd_item_protein.wd_item_id,
                duration=time.time() - start
                ))

            print('success')

        except Exception as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=self.gene_record.RS_protein,
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))

        end = time.time()
        print('Time elapsed:', end - start)


class GeneProteinEncodes(object):
    def __init__(self, gene_record):
        self.gene_record = GeneDataParser(gene_record)
        self.g_qid = WDProp2QIDSPARQL(prop='P351', string=self.gene_record.geneid).qid
        self.p_qid = WDProp2QIDSPARQL(prop='P352', string=self.gene_record.uniprotid).qid
        self.references = ReferenceStore()

    def encodes(self):
        start = time.time()
        if self.p_qid != 'None':
            print('Gene item {} and the protein item {} found...encoding now'.format(self.g_qid, self.p_qid))

            NCIB_gene_reference = self.references.uniprot_ref()
            encodes = [PBB_Core.WDItemID(value=self.p_qid, prop_nr='P688', references=[copy.deepcopy(NCIB_gene_reference)])]
            try:
                wd_gene = PBB_Core.WDItemEngine(wd_item_id=self.g_qid, data=encodes)
                #pprint.pprint(wd_gene.wd_json_representation)
                wd_gene.write(login)
                PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    main_data_id=self.g_qid,
                    exception_type='',
                    message='success{}'.format(self.g_qid + " encodes " + self.p_qid),
                    wd_id=wd_gene.wd_item_id,
                    duration=time.time() - start
                ))

                print("Success!")

            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    main_data_id=self.g_qid,
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=self.g_qid,
                    duration=time.time() - start
                ))

        if self.g_qid != 'None':
            print('Protein item {} and the gene item {} found...encoding now'.format(self.p_qid, self.g_qid))

            UniProt_reference = self.references.uniprot_ref()
            encoded_by = [PBB_Core.WDItemID(value=self.g_qid, prop_nr='P702', references=[copy.deepcopy(UniProt_reference)])]


            try:
                wd_protein = PBB_Core.WDItemEngine(wd_item_id=self.p_qid, data=encoded_by)
                #pprint.pprint(wd_protein.wd_json_representation)
                wd_protein.write(login)
                PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", '
                                                  '{wd_id}, {duration}'.format(
                    main_data_id=self.p_qid,
                    exception_type='',
                    message='success{}'.format(self.p_qid + " encoded by " + self.g_qid),
                    wd_id=wd_protein.wd_item_id,
                    duration=time.time() - start
                ))

                print("Success!")

            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", '
                                                   '{wd_id}, {duration}'.format(
                    main_data_id=self.p_qid,
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=self.p_qid,
                    duration=time.time() - start
                ))

        end = time.time()
        print('Time elapsed:', end - start)



try:
    login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
except Exception as e:
    print(e)
    print("could not log in")

#######Call Section######

print("Finding Bacterial Reference Genome...")
print("Standby...")
reference_genomes_list = NCBIReferenceGenomes()
#pprint.pprint(reference_genomes_list.tid_list)


for strain in reference_genomes_list.tid_list:
    pstrain = StrainDataParser(strain)

    if pstrain.strain_taxid == sys.argv[4]:

        print("Found", strain)
        print('Beginning {} bot run on {}'.format(sys.argv[3], pstrain.taxon_name))
        mgi_record = MyGeneInfoRestBatchQuery(strain).gene_record
        unip_record = UniProtRESTBatchQuery(strain).enzyme_record
        combined = MGI_UNIP_Merger(mgi=mgi_record, unip=unip_record)

        for gene in combined.mgi_unip_dict:
            if sys.argv[3] == 'genes':
                wd_gene = WDGeneItem(gene, strain)
                wd_gene.gene_item()
            if sys.argv[3] == 'proteins':
                wd_protein = WDProteinItem(gene, strain)
                wd_protein.protein_item()
            if sys.argv[3] == 'encoder':
                wd_encoder = GeneProteinEncodes(gene)
                wd_encoder.encodes()




