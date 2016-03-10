import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import pprint
import MicrobeBotWDFunctions as wdo
import time
__author__ = 'timputman'


def encodes(gene_record, login):
    """
    identifies microbial gene and protein items and links them via encodes (P688) and encoded by (P702) functions
    :param gene_record: gene record from MGI_UNIP_MERGER()
    :return: links gene and protein wikidata items.
    """
    start = time.time()
    #  find gene and protein qids
    gene_qid = wdo.WDSparqlQueries(prop='P351', string=gene_record['_id']).wd_prop2qid()
    protein_qid = wdo.WDSparqlQueries(prop='P352', string=gene_record['UNIPROT']).wd_prop2qid()
    # if a gene or protein item is not found skip this one
    if gene_qid is not None and protein_qid is not None:
        print('gene {} and protein {} found'.format(gene_qid, protein_qid))
        # generate reference and claim values for each item
        ncbi_gene_reference = wdo.reference_store(source='ncbi_gene', identifier=gene_record['_id'])
        gene_encodes = [PBB_Core.WDItemID(value=protein_qid, prop_nr='P688', references=[ncbi_gene_reference])]
        protein_encoded_by = [PBB_Core.WDItemID(value=gene_qid, prop_nr='P702', references=[ncbi_gene_reference])]
        # find and write items
        try:
            wd_encodes_item = PBB_Core.WDItemEngine(wd_item_id=gene_qid, data=gene_encodes)
            wd_encodes_item.write(login)

            PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['_id'],
            exception_type='',
            message='encodes claim written successfully',
            wd_id=wd_encodes_item.wd_item_id,
            duration=time.time() - start
            )
            )
            print('success')

        except Exception as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                main_data_id=gene_record['_id'],
                exception_type=type(e),
                message=e.__str__(),
                wd_id='',
                duration=time.time() - start
            ))
        try:
            wd_encoded_by_item = PBB_Core.WDItemEngine(wd_item_id=protein_qid, data=protein_encoded_by)
            wd_encoded_by_item.write(login)
            PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['UNIPROT'],
            exception_type='',
            message='encoded by claim written successfully',
            wd_id=wd_encoded_by_item.wd_item_id,
            duration=time.time() - start
            )
            )
            print('success')

        except Exception as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                main_data_id=gene_record['_id'],
                exception_type=type(e),
                message=e.__str__(),
                wd_id='',
                duration=time.time() - start
            ))

    end = time.time()
    print('Time elapsed:', end - start)
