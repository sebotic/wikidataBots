import MicrobeBotResources as MBR
import MicrobeBotGenes as MBG
import MicrobeBotProteins as MBP
import MicrobeBotEncoder as MBE
import pandas as pd
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
print('Retrieving current list of NCBI Bacterial Reference Genomes')
print('Standby...')
print('{} reference genomes retrieved'.format(genome_records.shape[0]))

# specify a genome from list to run the bot on
taxid = sys.argv[3]
spec_strain = genome_records[genome_records['taxid'] == int(taxid)]

# Retrieve gene and protein records from UniProt and Mygene.info by taxid

print('Retrieving gene records for {} taxid:{}'.format(spec_strain.iloc[0]['organism_name'], taxid))
gene_records = MBR.mgi_unip_data(taxid)  # PANDAS DataFrame
print('{} gene_records retrieved'.format(gene_records.shape[0]))
# Iterate through gene_records for reading and writing to Wikidata

for index, row in gene_records.iterrows():
    if sys.argv[4] == 'genes':
        print('commencing gene bot run')
        item = MBG.wd_item_construction(row, login)
    if sys.argv[4] == 'proteins':
        print('commencing protein bot run')
        item = MBP.wd_item_construction(row, login)
    if sys.argv[4] == 'encoder':
        print('commencing encoder bot run')
        item = MBE.encodes(row, login)


