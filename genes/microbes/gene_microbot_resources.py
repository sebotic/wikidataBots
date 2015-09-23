#!/usr/local/bin/python3

import pandas as pd
import json
import pprint


__author__ = 'timputman'


class ReferenceTaxonomyIDList(object):

    def __init__(self):

        self.col_names = ['tax_id', 'gene_id', 'status', 'RNA_access', 'RNA_gi', 'prot_access_version', 'prot_gi',
                          'genome_acess_version', 'genome_gi', 'genStart', 'genStop', 'orientation', 'assembly',
                          'mature_peptide_access_version', 'mature_peptide_gi', 'symbol']

        self.taxids = pd.read_csv("NCBI_FTP_SOURCE_FILES/assembly_summary.txt", sep="\t")
        self.gene2rs = pd.read_csv("NCBI_FTP_SOURCE_FILES/gene2refseq.txt", sep="\t", skiprows=1, names=self.col_names)
        self .merged_inner = ''

    def taxid_refs_pd(self):

        consol_tids = self.taxids[self.taxids["refseq_category"].str.contains("genome") == True]
        self.merged_inner = pd.merge(left=self.gene2rs, right=consol_tids, left_on='tax_id', right_on='taxid')
        a = self.merged_inner[['gene_id', 'taxid', 'species_taxid', 'organism_name', 'prot_gi', 'genome_acess_version',
                               'genStart', 'genStop', 'orientation', 'symbol', 'refseq_category']]

        return a.to_json(orient='records')


a = ReferenceTaxonomyIDList()
b = a.taxid_refs_pd()
c = json.loads(b)
pprint.pprint(c)