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

try:
    login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
except Exception as e:
    print(e)
    print("could not log in")


class ReferenceStore(object):
    def _init_(self):
        self.retrieved = self.retrieved_on()

    def retrieved_on(self):
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        return refRetrieved

    def uniprot_imported(self):
        """
        reference object to add to PBB_Core statements originating from UniProt database
        :return:
        """
        uniprotrefImported = PBB_Core.WDItemID(value='Q905695', prop_nr='P143', is_reference=True)
        uniprotrefImported.overwrite_references = True
        return uniprotrefImported

    def ncbi_gene_stated(self):
        """
        reference object to add to PBB_Core statements originating from NCBI Gene database
        :return:
        """
        NCBIgenerefStated = PBB_Core.WDItemID(value='Q20641742', prop_nr='P248', is_reference=True)
        NCBIgenerefStated.overwrite_references = True

        return NCBIgenerefStated

    def ncbi_gene_imported(self):
        """
        reference object to add to PBB_Core statements originating from NCBI Gene database
        :return:
        """
        NCBIgenerefimported = PBB_Core.WDItemID(value='Q20641742', prop_nr='P143', is_reference=True)
        NCBIgenerefimported.overwrite_references = True

        return NCBIgenerefimported

    def ncbi_taxonomy(self):
        """
        reference object to add to PBB_Core statements originating from NCBI Taxonomy database
        :return:
        """
        NCBItaxrefStated = PBB_Core.WDItemID(value='Q13711410', prop_nr='P248', is_reference=True)
        NCBItaxrefStated.overwrite_references = True
        return NCBItaxrefStated

    def swiss_prot(self):
        """
        reference object for data stated in Swiss-Prot
        :return:
        """
        swiss_prot_Stated = PBB_Core.WDItemID(value='Q2629752', prop_nr='P248', is_reference=True)
        swiss_prot_Stated.overwrite_references = True
        return swiss_prot_Stated

    def trembl(self):
        """
        reference object for data stated in TrEMBL
        :return:
        """
        trembl_prot_Stated = PBB_Core.WDItemID(value='Q22935315', prop_nr='P248', is_reference=True)
        trembl_prot_Stated.overwrite_references = True
        return trembl_prot_Stated


class WDProp2QIDSPARQL(object): #change
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
        """
        :param string: 'Q2458943' String value
        :return: QID 'Label'
        """
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

        :return: List of strain data lists e.g. [['species taxid1','strain taxid1','genus1', 'species1', 'strain1'],
                                                 ['species taxid2','strain taxid2','genus2', 'species2', 'strain2']]
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
        """
        generates an object from parsed strain data resulting from NCBIReferenceGenomes()
        :param strain_data:
        :return: object for each element of strain data
        """
        self.strain_data = strain_data
        self.species_taxid = str(self.strain_data[0])
        self.strain_taxid = self.strain_data[1]
        self.taxon_name = " ".join(self.strain_data[2:])
        self.genus = self.strain_data[2]
        self.species = self.strain_data[3]
        self.strain = self.strain_data[4]


class GeneDataParser(object):
    def __init__(self, gene_data):
        """
        generates an object from parsed gene data resulting from  MGI_UNIP_Merger()
        :param gene_data object from  MGI_UNIP_Merger():
        :return: object for each element of combined gene data
        """
        self.gene_data = gene_data

        if 'locus_tag' in self.gene_data.keys():
            self.locus_tag = self.gene_data['locus_tag']
        else:
            self.locus_tag = ''
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
        self.prot_rank = self.gene_data['prot_rank']


class MyGeneInfoRestBatchQuery(object):
    def __init__(self, strain_data):
        """
        Takes strain data from NCBIReferenceGenomes() and hits MyGene.info for all gene records by strain taxid
        :param strain_data from NCBIReferenceGenomes():
        :return: list of python dictionaries for each MyGene.info gene record by tax id
        """
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
                prot_rank = ''
                if 'uniprot' in i.keys():
                    if 'Swiss-Prot' in i['uniprot']:
                        prot_rank = 'Swiss-Prot'
                        if isinstance(i['uniprot']['Swiss-Prot'],str):
                            uniprot = i['uniprot']['Swiss-Prot']
                        else:
                            uniprot = i['uniprot']['Swiss-Prot'][0]

                    if 'TrEMBL' in i['uniprot']:
                        prot_rank = 'TrEMBL'
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
                    'ec_number': '',
                    'prot_rank': prot_rank,
                    'locus_tag': i['locus_tag']
                }
                mgi_data.append(wd_data)
        return mgi_data


class UniProtRESTBatchQuery(object):
    def __init__(self, strain_data):
        self.strain_taxid = StrainDataParser(strain_data).strain_taxid
        self.enzyme_record = self.download_taxon_protein_GO()

    def download_taxon_protein_GO(self):
        """
         Downloads the latest list of microbial proteins from UniProt, taxon specified by the strain tax id provided.
        :return: List of python dictionaries for each protein record from UniProt by Tax id
        """

        url = 'http://www.uniprot.org/uniprot/'

        params = dict(query=('organism:' + self.strain_taxid), format='tab',
                      columns='id,go(biological process),go(cellular component),go(molecular function),ec')
        r = requests.get(url=url, params=params)
        go_terms = r.text
        datareader = csv.reader(go_terms.splitlines(), delimiter="\t")
        next(datareader, None)
        uniprot_data = []

        for i in datareader:
            go_dict = dict()
            go_dict['uniprot'] = i[0]

            if i[4]:
                eclist = i[4].split(";")
                go_dict['ec_number'] = eclist

            if i[1]:
                bplist = i[1].split(";")  # P680
                bpgolist= []
                for item in bplist:
                    bpdict = {}
                    bp = item.split()
                    bpdict['goid'] = bp[-1][1:-1]
                    bpdict['goterm'] = " ".join(bp[:-1])
                    bpgolist.append(bpdict)
                go_dict['biological_process'] = bpgolist

            if i[2]:
                cclist = i[2].split(";")  # P680
                ccgolist= []
                for item in cclist:
                    ccdict = {}
                    cc = item.split()
                    ccdict['goid'] = cc[-1][1:-1]
                    ccdict['goterm'] = " ".join(cc[:-1])
                    ccgolist.append(ccdict)
                go_dict['cell_component'] = ccgolist

            if i[3]:
                mflist = i[3].split(";")  # P680
                mfgolist= []
                for item in mflist:
                    mfdict = {}
                    mf = item.split()
                    mfdict['goid'] = mf[-1][1:-1]
                    mfdict['goterm'] = " ".join(mf[:-1])
                    mfgolist.append(mfdict)
                go_dict['molecular_function'] = mfgolist

            uniprot_data.append(go_dict)
        return uniprot_data


class MGI_UNIP_Merger(object):
    def __init__(self, mgi, unip):
        """
        combines data from UniProt and MyGene.info into 1 dictionary per gene entry based
        on UniProt ID as lookup key
        :param mgi: single entry from MyGene.info
        :param unip: All hits from UniProt
        :return: list of single consolidated gene record dictionaries by tax id
        """
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


class WDOrganismItem(object):
    def __init__(self, gene_record, strain_record):
        """
        searches for and creates, if necessary, strain and species items
        :param gene_record: gene record output from MGI_UNIP MERGER
        :param strain_record: corresponding strain_record output from NCBIReferenceGenomes()
        :return: creates new wikidata item fro species (create_species_item()) or strain (create_strain_item())
        """
        self.strain_record = StrainDataParser(strain_record)
        self.refseqid = GeneDataParser(gene_record).RS_genome
        self.references = ReferenceStore()
        self.species_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.species_taxid).qid
        self.strain_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.strain_taxid).qid

    def create_species_item(self):
        species_description = "species of prokaryote"
        alias = self.strain_record.genus[0] + ". " + self.strain_record.species
        NCIB_tax_ref = self.references.ncbi_taxonomy()

        if self.species_qid != 'None':
            print(self.strain_record.genus + " " + self.strain_record.species + " already exists\t" + self.species_qid)
            statements = []
            statements.append(PBB_Core.WDString(value=self.strain_record.species_taxid, prop_nr='P685', references=[copy.deepcopy(NCIB_tax_ref)])) # Species taxid
            statements.append(PBB_Core.WDString(value=self.strain_record.genus + " " + self.strain_record.species, prop_nr='P225', references=[copy.deepcopy(NCIB_tax_ref)])) # Taxon name
            statements.append(PBB_Core.WDItemID(value='Q7432', prop_nr='P105', references=[copy.deepcopy(NCIB_tax_ref)])) #Taxon Rank species
            statements.append(PBB_Core.WDString(value=self.refseqid, prop_nr='P2249', references=[copy.deepcopy(NCIB_tax_ref)])) #RefSea GenomeId
            try:
                wd_item = PBB_Core.WDItemEngine(wd_item_id=self.species_qid, data=statements)
                wd_item.set_aliases(alias)
                wd_item.set_description(species_description)
                #pprint.pprint(wd_item.get_wd_json_representation())
                #wd_item.write(login)

            except Exception as e:
                print(e)

    def create_strain_item(self):
        strain_description = "bacterial strain"
        alias = self.strain_record.strain
        NCIB_tax_ref = self.references.ncbi_taxonomy()

        if self.strain_qid != 'None':
            #print(self.strain_record.genus + " " + self.strain_record.s + " " +  self.strain_record.strain + "  already exists\t" + self.species_qid)
            statements = []
            statements.append(PBB_Core.WDString(value=self.strain_record.strain_taxid, prop_nr='P685', references=[copy.deepcopy(NCIB_tax_ref)])) # Species taxid
            statements.append(PBB_Core.WDString(value=self.strain_record.genus + " " + self.strain_record.species, prop_nr='P225', references=[copy.deepcopy(NCIB_tax_ref)])) # Taxon name
            statements.append(PBB_Core.WDItemID(value='Q7432', prop_nr='P105', references=[copy.deepcopy(NCIB_tax_ref)])) #Taxon Rank species

            try:
                wd_item = PBB_Core.WDItemEngine(wd_item_id=self.species_qid, data=statements)
                wd_item.set_aliases(alias)
                wd_item.set_description(strain_description)
                #pprint.pprint(wd_item.get_wd_json_representation())
                #wd_item.write(login)

            except Exception as e:
                print(e)


class WDGeneItem(object):
    def __init__(self, gene_record, strain_record):
        """
        locates and edits too, or creates new wikidata item for microbial genes
        :param gene_record: gene record output from MGI_UNIP MERGER
        :param strain_record: corresponding strain_record output from NCBIReferenceGenomes()
        :return: creates or edits bacterial gene items in wikidata
        """
        self.gene_record = GeneDataParser(gene_record)
        self.strain_record = StrainDataParser(strain_record)
        self.references = ReferenceStore()

    def gene_item(self):
        """
        Write gene items using dictionary from wd_parse_mgi(self):
        :return:
        """
        if self.gene_record.locus_tag:
            item_name = self.gene_record.name + "\t" + self.gene_record.locus_tag
            alias_list = [self.gene_record.gene_symbol, self.gene_record.locus_tag]
            strain_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.strain_taxid).qid
            strain_label = WDQID2LabelSPARQL(qid=strain_qid).label
            description = "microbial gene found in " + strain_label


            ncbi_gene_reference =[[self.references.ncbi_gene_stated(), self.references.ncbi_gene_imported(),
                                  self.references.retrieved_on()]]

            statements = list()
            statements.append(PBB_Core.WDItemID(value=strain_qid, prop_nr='P703',
                                                references=ncbi_gene_reference)) #Found in taxon
            statements.append(PBB_Core.WDString(value=self.gene_record.geneid, prop_nr='P351',
                                                references=ncbi_gene_reference))
            if self.gene_record.locus_tag:



                statements.append(PBB_Core.WDString(value=self.gene_record.locus_tag, prop_nr='P2393',
                                                    references=ncbi_gene_reference))


            statements.append(PBB_Core.WDItemID(value='Q7187', prop_nr='P279',
                                                references=ncbi_gene_reference))
            statements.append(PBB_Core.WDString(value=self.gene_record.genstart, prop_nr='P644',
                                                references=ncbi_gene_reference))
            statements.append(PBB_Core.WDString(value=self.gene_record.genstop, prop_nr='P645',
                                                references=ncbi_gene_reference))
            if self.gene_record.strand == '1':
                statements.append(PBB_Core.WDItemID(value='Q22809680', prop_nr='P2548',
                                                    references=ncbi_gene_reference))
            if self.gene_record.strand == '-1':
                statements.append(PBB_Core.WDItemID(value='Q22809711', prop_nr='P2548',
                                                    references=ncbi_gene_reference))

            start = time.time()

            try:
                wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=statements,
                                                     use_sparql=True)
                wd_item_gene.set_label(item_name)
                wd_item_gene.set_description(description)
                wd_item_gene.set_aliases(alias_list)
                #pprint.pprint(wd_item_gene.get_wd_json_representation())
                if self.gene_record.locus_tag:
                    wd_item_gene.write(login)

                new_mgs = ''
                if wd_item_gene.create_new_item:
                    new_mgs = ': New item'
                else:
                    new_mgs = ': Eddited_item'
                PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", '
                                                  '"{message}", {wd_id}, {duration}'.format(
                    main_data_id=self.gene_record.geneid,
                    exception_type='',
                    message='success{}'.format(new_mgs),
                    wd_id=wd_item_gene.wd_item_id,
                    duration=time.time() - start
                    ))

                print('success')

            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", '
                                                   '"{message}", {wd_id}, {duration}'.format(
                            main_data_id=self.gene_record.geneid,
                            exception_type=type(e),
                            message=e.__str__(),
                            wd_id='',
                            duration=time.time() - start
                        ))

            end = time.time()
            print('Time elapsed:', end - start)
        else:
            pass


class WDProteinItem(object):
    def __init__(self, gene_record, strain_record):
        """
        locates and edits to, or creates new wikidata item for microbial proteins
        :param gene_record: gene record output from MGI_UNIP MERGER
        :param strain_record: corresponding strain_record output from NCBIReferenceGenomes()
        :return: creates or edits bacterial protein items in wikidata
        """
        self.gene_record = GeneDataParser(gene_record)
        self.strain_record = StrainDataParser(strain_record)
        self.references = ReferenceStore()
        self.final_protein_statements = []

    def protein_item(self):

        if self.gene_record.locus_tag:
            item_name = self.gene_record.name + "\t" + self.gene_record.locus_tag
            alias_list = [self.gene_record.protein_symbol]
            strain_qid = WDProp2QIDSPARQL(prop='P685', string=self.strain_record.strain_taxid).qid
            strain_label = WDQID2LabelSPARQL(qid=strain_qid).label
            description = "microbial protein found in " + strain_label
            uniprot_protein_reference =[]
            if self.gene_record.prot_rank == 'Swiss-Prot':
                uniprot_protein_reference.append(self.references.swiss_prot())
            if self.gene_record.prot_rank == 'TrEMBL':
                uniprot_protein_reference.append(self.references.trembl())

            uniprot_protein_reference.append(self.references.uniprot_imported())
            uniprot_protein_reference.append(self.references.retrieved_on())

            statements = {}
            statements['found_in'] = [PBB_Core.WDItemID(value=strain_qid, prop_nr='P703', references=[uniprot_protein_reference])] #Found in taxon
            statements['uniprot'] = [PBB_Core.WDString(value=self.gene_record.uniprotid, prop_nr='P352',  references=[uniprot_protein_reference])]
            statements['proteinid'] = [PBB_Core.WDString(value=self.gene_record.RS_protein, prop_nr='P637',  references=[uniprot_protein_reference])]
            statements['subclass'] = [PBB_Core.WDItemID(value='Q8054', prop_nr='P279',  references=[uniprot_protein_reference])]
            statements['molecular_function'] = []
            statements['cell_component'] = []
            statements['biological_process'] = []
            statements['ec_number'] = []

            if self.gene_record.ec_number:
                for i in self.gene_record.ec_number:
                    statements['ec_number'].append(PBB_Core.WDString(value=i, prop_nr='P591',  references=[uniprot_protein_reference]))

            if self.gene_record.GO_MF:
                molfunc = GOTerms(self.gene_record.GO_MF)
                for i in molfunc.go_qid_list():
                    statements['molecular_function'].append(PBB_Core.WDItemID(value=i, prop_nr='P680', references=[uniprot_protein_reference]))

            if self.gene_record.GO_BP:
                bioproc = GOTerms(self.gene_record.GO_BP)
                for i in bioproc.go_qid_list():
                    statements['biological_process'].append(PBB_Core.WDItemID(value=i, prop_nr='P682', references=[uniprot_protein_reference]))

            if self.gene_record.GO_CC:
                celcomp = GOTerms(self.gene_record.GO_CC)
                for i in celcomp.go_qid_list():
                    statements['cell_component'].append(PBB_Core.WDItemID(value=i, prop_nr='P681', references=[uniprot_protein_reference]))

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
        else:
            pass


class GOTerms(object):
    def __init__(self, goterms):
        self.goterms = goterms

    def go_qid_list(self):
        goqidlist = []
        if self.goterms:
            godict = {}
            for gt in self.goterms:
                godict['go_qid'] = WDProp2QIDSPARQL(prop='P686', string=gt['goid']).qid
                godict['go_label'] = WDQID2LabelSPARQL(qid=godict['go_qid']).label
                if gt['goterm'] == godict['go_label']:
                    goqidlist.append(godict['go_qid'])
        return goqidlist


class GeneProteinEncodes(object):
    def __init__(self, gene_record):
        """
        identifies microbial gene and protein items and links them via encodes (P688) and encoded by (P702) functions
        :param gene_record: gene record from MGI_UNIP_MERGER()
        :return: links gene and protein wikidata items.
        """
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





