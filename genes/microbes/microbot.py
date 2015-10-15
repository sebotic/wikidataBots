import csv
import requests
import urllib.request
import pprint
import sys
import PBB_Core
import PBB_login
from maintenance import go_cleaner
import pandas as pd


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
        #assembly = open("bac_assembly_summary_tail.txt", "r")

        datareader = csv.reader(assembly.read().decode().splitlines(), delimiter="\t")
        #datareader = csv.reader(assembly.read().splitlines(), delimiter="\t")
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


class WDGeneProteinItem(object):
    def __init__(self):

        self.mgi_genes = self.gain_refseq_mgi()

    def gain_refseq_mgi(self):
        """
        Query mygene.info by tax id.  Return all gene records for every taxid entered in json
        :return:
        """

        url = 'http://mygene.info/v2/query/'
        orgid = pd.read_csv("chlam_summ.txt", sep="\t")   #don't forget this is just for chlamydia right now.
                                                          # Full run will include the output from download_parse_
                                                          # reference_genome_data()
        orgidl = orgid['taxid'].tolist()
        params = dict(q="__all__", species=orgidl, entrezonly="true", size="50", fields="all")  #experimenting with 10 genes
        r = requests.get(url, params)

        return r.json()

    def wd_gene_items(self):
        """
        Go through the mygene.info json and format label and description names for genes.
        Generate gene items using PBB_Core.wd_item_enging()

        :param genes_json:
        :return:
        """
        content = self.mgi_genes['hits']

        for entry in content:

            if entry['type_of_gene'] != 'protein-coding':
                continue
            else:
                if "hypothetical protein" == entry['name']:
                    item_name = entry['name'] + " " + entry['symbol']
                else:
                    item_name = entry['name']

            taxid = str(entry['taxid'])
            parent = WDProp2QID(taxid, '685')

            q2label = WDQID2Label(parent.qid)
            description = "microbial gene found in " + q2label.label
            parent_taxon = PBB_Core.WDItemID(value=parent.qid, prop_nr='P703') #Found in taxon
            symbol = PBB_Core.WDString(value=entry['symbol'], prop_nr='P353')
            geneid = PBB_Core.WDString(value=entry['_id'], prop_nr='P351')

            if not isinstance(entry['accession']['protein'], str):
                proteinid = PBB_Core.WDString(value=entry['accession']['protein'][1], prop_nr='P637')

            else:
                proteinid = PBB_Core.WDString(value=entry['accession']['protein'], prop_nr='P637')

            try:
                wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=[parent_taxon, symbol, geneid,
                                                                                           proteinid])
                login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
                wd_item.set_description(description)
                pprint.pprint(wd_item.get_wd_json_representation())
                wd_item.write(login)
                
            except Exception as e:
                print(e)
                go_cleaner.GOCleaner(e)


