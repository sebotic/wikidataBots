import MicrobeBotResources as MBR
import MicrobeBotGenes as MBG
import MicrobeBotProteins as MBP
import MicrobeBotEncoder as MBE
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_login



__author__ = 'timputman'

if len(sys.argv) < 4:
    print("   You did not supply the proper arguments!")
    print("   Usage: MicrobeBotModularPackage.py <Wikidata user name> <Wikidata Password> <run number> <domain "
          "i.e. genes/proteins/encode_genes/encode_proteins>" )
    sys.exit()
else:
    pass


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for c in range(0, len(l), n):
        yield l[c:c+n]

# Login to Wikidata with bot credentials
login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])

# Retrieve Current Bacterial Reference Genomes from NCBI
genome_records = MBR.get_ref_microbe_taxids()
ref_taxids = genome_records['taxid'].tolist()
# break up list of taxids into chunks of 5 for subruns
count = 0
runs_list = chunks(ref_taxids, 5)
taxids = {}
for i in runs_list:
    count += 1
    taxids['run{}'.format(count)] = i

print('Retrieving current list of NCBI Bacterial Reference Genomes')
print('Standby...')
print('{} reference genomes retrieved'.format(genome_records.shape[0]))

# sys.argv[3] (run1, run2, etc...) specifies a list of taxids from dict(taxids)to run the bot on
for tid in taxids[sys.argv[3]]:
    spec_strain = genome_records.loc[genome_records['taxid'] == int(tid)]
    # Retrieve gene and protein records from UniProt and Mygene.info by taxid
    print('Retrieving gene records for {} taxid:{}'.format(spec_strain.iloc[0]['organism_name'], tid))
    gene_records = MBR.mgi_unip_data(tid)  # PANDAS DataFrame
    print('{} gene_records retrieved'.format(gene_records.shape[0]))
    # Iterate through gene_records for reading and writing to Wikidata
    print('Commencing for {} taxid:{}'.format(spec_strain.iloc[0]['organism_name'], tid))
    for index, row in gene_records.iterrows():
        if sys.argv[4] == 'genes':
            item = MBG.wd_item_construction(row, login)
        if sys.argv[4] == 'proteins':
            item = MBP.wd_item_construction(row, login)
        if sys.argv[4] == 'encoder':
            item = MBE.encodes(row, login)

