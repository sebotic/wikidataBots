import sys
import os
import pprint
import MicrobeBotModulePackage as MB
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_login


__author__ = 'timputman'


if len(sys.argv) < 5:
    print("   You did not supply the proper arguments!")
    print("   Usage: MicrobeBotModularPackage.py <Wikidata user name> <Wikidata Password> <domain i.e. genes/proteins/encode_genes/encode_proteins> <microbial strain taxid>")
    sys.exit()
else:
    pass

taxids = [471472, 272561, 300852, 208964, 107806, 272624, 85962, 224326, 122586, 243275, 192222, 242231, 585057, 177416, 214092, 272621, 160488, 83332, 93061, 198214, 525284]

print("Finding Bacterial Reference Genome...")
print("Standby...")
reference_genomes_list = MB.NCBIReferenceGenomes()
pprint.pprint(reference_genomes_list.tid_list)

count = 0
for strain in reference_genomes_list.tid_list:
    pstrain = MB.StrainDataParser(strain)
    for tid in taxids:
        if pstrain.strain_taxid == str(tid):

            print("Found", strain)
            print('Beginning {} bot run on {}'.format(sys.argv[3], pstrain.taxon_name))

            mgi_record = MB.MyGeneInfoRestBatchQuery(strain).gene_record
            unip_record = MB.UniProtRESTBatchQuery(strain).enzyme_record
            combined = MB.MGI_UNIP_Merger(mgi=mgi_record, unip=unip_record)
            print_test = []
            count = 0
            for gene in combined.mgi_unip_dict:
                count += 1
                print(count)
                if sys.argv[3] == 'genes':
                    wd_gene = MB.WDGeneItem(gene, strain)
                    wd_gene.gene_item()
                if sys.argv[3] == 'proteins':
                    wd_protein = MB.WDProteinItem(gene, strain)
                    wd_protein.protein_item()
                if sys.argv[3] == 'encoder':
                    wd_encoder = MB.GeneProteinEncodes(gene)
                    wd_encoder.encodes()

