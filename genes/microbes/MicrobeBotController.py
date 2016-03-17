import MicrobeBotResources as MBR
import MicrobeBotGenes as MBG
import MicrobeBotProteins as MBP
import MicrobeBotEncoder as MBE
import MicrobeBotWDFunctions as wdo
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
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
print('Retrieving current list of NCBI Bacterial Reference Genomes')
print('Standby...')
genome_records = MBR.get_ref_microbe_taxids()
ref_taxids = genome_records['taxid'].tolist()

# break up list of taxids into chunks of 5 for subruns
count = 0
runs_list = chunks(ref_taxids, 5)

taxids = {}
for i in runs_list:
    count += 1
    taxids['run{}'.format(count)] = i

print('{} reference genomes retrieved'.format(genome_records.shape[0]))

# sys.argv[3] (run1, run2, etc...) specifies a list of taxids from dict(taxids)to run the bot on

for tid in taxids[sys.argv[3]]:
    spec_strain = genome_records.loc[genome_records['taxid'] == int(tid)]
    # Check for the organism wikidata item and skip if not created
    if spec_strain.iloc[0]['wd_qid'] is 'None':
        print('No Wikidata item for {}'.format(spec_strain['organism_name']))
        continue
    # Retrieve gene and protein records from UniProt and Mygene.info by taxid
    print('Retrieving gene records for {} taxid:{}'.format(spec_strain.iloc[0]['organism_name'], tid))
    gene_records = MBR.mgi_qg_resources(tid)  # PANDAS DataFrame
    print('{} gene_records retrieved'.format(len(gene_records)))
    # Iterate through gene_records for reading and writing to Wikidata
    print('Commencing {} bot run  for {}'.format(sys.argv[4], spec_strain.iloc[0]['organism_name']))
    gene_count = 0
    for record in gene_records:
        gene_count += 1
        print('{}/{}'.format(gene_count, len(gene_records)))
        if sys.argv[4] == 'genes':
            MBG.wd_item_construction(record, spec_strain, login)
        if sys.argv[4] == 'proteins':
            MBP.wd_item_construction(record, spec_strain, login)
        if sys.argv[4] == 'encoder':
            MBE.encodes(record, login)

