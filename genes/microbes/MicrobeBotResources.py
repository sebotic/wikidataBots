import urllib.request
import requests
import pandas as pd
from pandas.io.json import json_normalize

__author__ = 'timputman'


def get_ref_microbe_taxids():
    """
    Download the latest bacterial genome assembly summary from the NCBI genome ftp site
    and generate a list of relevant data for strain items based on taxids of the bacterial reference genomes.
    :return: List of strain data lists e.g. [['species taxid1','strain taxid1','genus1', 'species1', 'strain1'],
                                             ['species taxid2','strain taxid2','genus2', 'species2', 'strain2']]
    """
    assembly = urllib.request.urlretrieve("ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt")
    data = pd.read_csv(assembly[0], sep="\t")
    data = data[data['refseq_category'] == 'reference genome']
    return data


def mgi_unip_data(taxid):

    def uniprot_rest_go_ec():
        """
         Downloads the latest list of microbial proteins from UniProt, taxon specified by the strain tax id provided.
        :return: List of python dictionaries for each protein record from UniProt by Tax id
        """
        url = 'http://www.uniprot.org/uniprot/?query=organism%3A{}&columns=id%2Cgo%28biological+' \
              'process%29%2Cgo%28cellular+component%29%2Cgo%28molecular+function%29%2Cec&format=tab'.format(taxid)
        go_terms = urllib.request.urlretrieve(url)
        return pd.read_csv(go_terms[0], sep="\t")

    def mygeneinfo_rest_query():
        """
        Downloads the latest list of microbial genes by taxid to a pandas dataframe
        :return: pandas data frame
        """
        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=taxid, entrezonly="true", size="10000", fields="all")
        data = requests.get(url=url, params=params).json()
        # Reads mgi json hits into dataframe
        res = [json_normalize(hit) for hit in data["hits"]]
        df = pd.concat(res).reset_index(drop=True)
        df['Combined_ID'] = df[['uniprot.Swiss-Prot','uniprot.TrEMBL']].fillna('').sum(axis=1)
        return df

    # joins dataframes from uniprot and mgi on the uniprot id
    return pd.merge(uniprot_rest_go_ec(), mygeneinfo_rest_query(), how='inner',
                    left_on='Entry', right_on='Combined_ID')
