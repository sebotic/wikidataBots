import csv
import requests
import urllib.request
import pprint
import sys
import PBB_Core
import PBB_login
from collections import defaultdict
import ast
import gzip
import time

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
        eng_label = resp['entities'][qid]['labels']['en']['value']

        return eng_label


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
        return "Q" + str(a['items'][0])


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
        for thing in all_strain_data:

            if thing[0] == '813': # This is a testing filter to restrict bot run to chlamydia only
                return [thing]

        #return all_strain_data


class WDStrainItem(object):
    def __init__(self, ref_orgs):

        self.login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
        self.ref_orgs = ref_orgs

    def wd_strain_genome_items(self):
        """
        Generate item for each bacterial strain in wikidata
        :return:
        """
        genomes = list(self.ref_orgs)

        description = "bacterial strain"

        for i in genomes:

            try:
                item_name = i[2]
                alias = [i[-1]]
                spec_tid = str(i[0])
                parent_qid = WDProp2QID(spec_tid, '685')
                parent_taxon = PBB_Core.WDItemID(value=parent_qid.qid, prop_nr='P171')
                tid = str(i[1])
                taxid = PBB_Core.WDString(value=tid, prop_nr='P685')
                taxonname = PBB_Core.WDString(value=i[2], prop_nr='P225')
                instance_of = PBB_Core.WDItemID(value='Q855769', prop_nr='P31')
                wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=[taxid, taxonname,
                                                                                            parent_taxon,
                                                                                             instance_of])
                wd_item.set_aliases(alias)
                wd_item.set_description(description)
                pprint.pprint(wd_item.get_wd_json_representation())
                wd_item.write(self.login)

            except IndexError:
                print("{} didn't have a parent".format(i[2]))

    def wd_species_items(self):
        species = list(self.ref_orgs)
        description = "species of prokaryote"

        for i in species:
            species_all = i[2].split(" ")
            species = " ".join(species_all[0:2])
            item_name = species
            alias = [i[-1]]
            spec_tid = str(i[0])
            species_taxid = PBB_Core.WDString(value=spec_tid, prop_nr='P685')
            taxonname = PBB_Core.WDString(value=species, prop_nr='P225')
            instance_of = PBB_Core.WDItemID(value='Q16521', prop_nr='P31')
            wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=[species_taxid, taxonname,
                                                                                         instance_of])
            wd_item.set_aliases(alias)
            wd_item.set_description(description)
            pprint.pprint(wd_item.get_wd_json_representation())
            #wd_item.write(self.login)


class WDGeneProteinItemDownload(object):
    def __init__(self, ref_orgs):
        self.ref_orgs = ref_orgs
        self.mgi_genes = self.gain_refseq_mgi()
        self.wd_dict = self.wd_parse_mgi()
        self.uniprot_go = self.download_taxon_protein_GO()
        self.uniprot_dict = self.parse_uniprot_data()
        self.genpos = self.gene2refseq2refonly()
        self.combo_mu = self.combine_mgi_uniprot_dicts()
    def gain_refseq_mgi(self):
        """
        Query mygene.info by tax id.  Return all gene records for every taxid entered in json
        :return:
        """

        url = 'http://mygene.info/v2/query/'

        genomes = list(self.ref_orgs)

        for i in genomes:
            tax_list = []
            orgidl = i[1]
            params = dict(q="__all__", species=orgidl, entrezonly="true", size="1000", fields="all")
            r = requests.get(url, params)
            tax_list.append(r.json())
            return tax_list # Yield will return a list for each taxid

    def wd_parse_mgi(self):
        """
        Go through the mygene.info json and format label and description names for genes.
        Generate gene items using PBB_Core.wd_item_enging()

        :param genes_json:
        :return:
        """
        content = self.mgi_genes
        hits = content[0]['hits']
        mgi_data = []
        for i in hits:
            if i['type_of_gene'] != 'protein-coding':
                continue
            else:
                if "hypothetical protein" == i['name']:
                    name = i['name'] + " " + i['symbol']
                else:
                    name = i['name']
                try:
                    uniprot = i['uniprot']['Swiss-Prot']
                except Exception:
                    uniprot = i['uniprot']['TrEMBL']

                taxid = str(i['taxid'])
                strain = WDProp2QID(taxid, '685')
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
                    'RSgenomic': i['refseq']['genomic'],
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

        genomes = list(self.ref_orgs)

        for i in genomes:
            orgidl = i[1]
            params = dict(query=('organism:' + orgidl), format='tab', columns='id,go(biological process),go(cellular component),go(molecular function)')
            r = requests.get(url, params=params)
            return r.text

    def parse_uniprot_data(self):

        content = self.uniprot_go
        datareader = csv.reader(content.splitlines(), delimiter="\t")
        uniprot_data = []

        for i in datareader:
            go_dict = {
                'Uniprotid': i[0],
                'biological_process': i[1], # biological process P682
                'cell_component': i[2], # cell component P681
                'molecular_function': i[3] # molecular function P680
            }
            uniprot_data.append(go_dict)
        return uniprot_data

    def gene2refseq2refonly(self):
        """
        Download and parse the gene2refseq file from NCBI and return genomic position data for the microbial reference genome genes
        using the output from download_parse_reference_genome_data() as a taxid lookup table

        :param tid_list: the output from dowload_parse_reference_genome_data():
        :return:
        """
        genomes = list(self.ref_orgs)

        #urllib.request.urlretrieve("ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2refseq.gz", "gene2refseq.gz")
        with gzip.open("gene2refseq_ctrachd.gz", "rt") as f:

            datareader = csv.reader(f, delimiter="\t")
            ncbi_data = []
            for tid in genomes:

                for i in datareader:

                    if i[0] == tid[1]:

                        if i[11] == '+':
                            strand = 1
                        else:
                            strand = -1
                        ncbi_dict = {
                            '_geneid': i[1],
                            'genstart': i[9],
                            'genstop': i[10],
                            'orientation': strand
                        }
                        ncbi_data.append(ncbi_dict)
            return ncbi_data

    def combine_mgi_uniprot_dicts(self):
        mgi = self.wd_dict
        unip = self.uniprot_dict
        out = open("mgi_uniprot_combined.dict", "w")

        result = defaultdict(dict)
        mgi_uniprot = []
        for d in mgi:
            result[d['uniprot']].update(d)
        for d in unip:
            result[d['Uniprotid']].update(d)
        for k,v in result.items():
            print(v, file=out) # This writes to a file for now.  Might be better to use pickle to load pyobj
            mgi_uniprot.append(v)
        return mgi_uniprot


class WDWriteGeneProteinItems(object):
    def __init__(self):
        self.dbdata = open("mgi_uniprot_combinedhead100.dict", "r")

    def write_gene_item(self):
        """
        Write gene items using dictionary from wd_parse_mgi(self):
        :return:
        """
        zwd_write_data = self.dbdata
        for i in zwd_write_data:
            start = time.time()
            wd_write_data= ast.literal_eval(i)
            alias_list = [wd_write_data['gene_symbol']]
            found_in = PBB_Core.WDItemID(value=wd_write_data['strain'], prop_nr='P703') #Found in taxon
            symbol = PBB_Core.WDString(value=wd_write_data['gene_symbol'], prop_nr='P353')
            geneid = PBB_Core.WDString(value=wd_write_data['_geneid'], prop_nr='P351')


            try:
                wd_item_gene = PBB_Core.WDItemEngine(item_name=wd_write_data['name'], domain='genes', data=[found_in, symbol, geneid])
                PBB_Core.WDItemEngine.log(level='INFO', message="Gene item error")
                qid1 = WDProp2QID(wd_write_data['_geneid'], '351')
                qid1 = qid1.qid

            except Exception as e:
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=qid1,
                        exception_type='',
                        message='Gene item error',
                        wd_id='',
                        duration=time.time() - start
                    ))
                continue

