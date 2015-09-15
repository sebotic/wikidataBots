#!/usr/local/bin/python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import requests
import json
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
import PBB_Functions


__author__ = 'timputman'

taxonomyid = sys.argv[1]


class EntrezGeneJson:

    def __init__(self, taxonomy=''):
        """
        This is the resource specific portion of the gene microbot.
        It uses the Entrez API to take an NCBI taxonomy ID, return
        all NCBI Gene Database IDs linked to that taxID, and
        then queries the Gene DB for the gene records.
        """
        self.content = {}
        self.taxonomy = taxonomy
        self.elinks = self.download_microbe_links()
        self.genes = self.gene_ids_gene_data(self.elinks)

    def download_microbe_links(self):

        """
        generate list of gene ids from genbank associated with input taxID using Entrez API's elink

        """

        elink_param = dict(db="gene", dbfrom="taxonomy", cmd="neighbor", id=self.taxonomy, retmode="json")
        elink_resp = requests.post('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?', params=elink_param)
        elink_hit = elink_resp.json()
        elink_parsed_json = json.loads(json.dumps(elink_hit))
        return elink_parsed_json['linksets'][0]['linksetdbs'][0]['links']

    def gene_ids_gene_data(self, elinks):
        """
        use list of gene ids from download_microbe links to query NCBI gene database using Entrez API's esummary
        """

        for i in range(0, len(self.elinks), 20):
            id_list = elinks[i:i + 20]
            id_string = ", ".join(repr(e) for e in id_list)
            esum_param = dict(db="gene", id=id_string, retmode="json")
            esum_resp = requests.post('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?', params=esum_param)
            esum_hit = esum_resp.json()
            esum_parsed_json = json.loads(json.dumps(esum_hit))
            for k, v in esum_parsed_json['result'].items():
                if 'uids' != k:
                    self.content[k] = v
        return self.content


class WDFormatJson(object):

    all_list = []

    def __init__(self, geneJ):
        """
        converts output of EntrezGeneJson to list of dictionaries with relevant Wikidata
        microbial gene item data
        :param geneJ:
        :return:
        """
        self.geneJ = geneJ

    def pull_rel_wd_data(self):

        for k, v in self.geneJ.items():
            data_dict = {
                'name': v['name'],
                'uid': v['uid'],
                'taxid': v['organism']['taxid'],
                'organism': v['organism']['scientificname']}
            try:
                data_dict['gen_start'] = v['genomicinfo'][0]['chrstart']
            except:
                data_dict['gen_start'] = "null"
            try:
                data_dict['gen_stop'] = v['genomicinfo'][0]['chrstart']
            except:
                data_dict['gen_stop'] = "null"

            WDFormatJson.all_list.append(data_dict)

        return WDFormatJson.all_list


test = EntrezGeneJson(taxonomyid).genes
test2 = WDFormatJson(test).pull_rel_wd_data()

for i in test2:
    print(i)