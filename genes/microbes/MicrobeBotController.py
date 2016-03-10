import MicrobeBotResources as MBR
import MicrobeBotGenes as MBG
import MicrobeBotProteins as MBP

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_login
import sys

__author__ = 'timputman'

if len(sys.argv) < 4:
    print("   You did not supply the proper arguments!")
    print("   Usage: MicrobeBotModularPackage.py <Wikidata user name> <Wikidata Password> <taxid> <domain "
          "i.e. genes/proteins/encode_genes/encode_proteins>" )
    sys.exit()
else:
    pass

# Login to Wikidata with bot credentials
login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])

# Retrieve Current Bacterial Reference Genomes from NCBI
genome_records = MBR.get_ref_microbe_taxids()
# specify a genome from list to run the bot on
taxid = sys.argv[3]
spec_strain = genome_records[genome_records['taxid'] == int(taxid)]

# Retrieve gene and protein records from UniProt and Mygene.info by taxid
gene_records = MBR.mgi_unip_data(taxid)  # PANDAS DataFrame
# Iterate through gene_records for reading and writing to Wikidata

for index, row in gene_records.iterrows():
    if sys.argv[4] == 'genes':
        item = MBG.wd_item_construction(row, login)
    if sys.argv[4] == 'proteins':
        item = MBP.wd_item_construction(row, login)

