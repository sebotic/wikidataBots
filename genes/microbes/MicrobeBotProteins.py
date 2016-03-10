import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import pprint
import MicrobeBotWDFunctions as wdo
import pandas as pd
import time

__author__ = 'timputman'


def parse_go_terms(goclass):
    """
    parses the tsv formated result from uniprot REST API
    :param goclass:
    :return:
    """
    if pd.notnull(goclass):
        goclass = goclass.split(';')
        goqidlist = []
        for i in goclass:
            go = i.split()
            goid = go[-1][1:-1]
            goterm = " ".join(go[:-1])
            go_qid = wdo.WDSparqlQueries(prop='P686', string=goid).wd_prop2qid()
            go_label = wdo.WDSparqlQueries(qid=go_qid).wd_qid2label()
            if goterm == go_label:
                goqidlist.append(go_qid)
        # returns list of go term qids
        return goqidlist


def wd_item_construction(gene_record, login):
    """
    identifies and modifies or writes new wd items for proteins
    :param gene_record: pandas dataframe
    :param login: bot account login credentials
    :return: PBB_Core wd item object
    """
    gene_record = gene_record
    # gets wd item qid for microbe protein is found in
    strain_qid = wdo.WDSparqlQueries(string=gene_record['taxid'], prop='P685').wd_prop2qid()
    # gets WD Item label for parent microbe based on qid
    strain_label = wdo.WDSparqlQueries(qid=strain_qid).wd_qid2label()
    item_description = 'microbial protein found in {}'.format(strain_label)
    item_name = gene_record['name'] + "\t" + gene_record['locus_tag']

    def protein_item_statements():
        """
        construct list of referenced statements to past to PBB_Core Item engine
        :return:
        """
        uniprot_reference = wdo.reference_store(source='uniprot', identifier=gene_record['Combined_ID'])

        WD_String_CLAIMS = {'P637': str(gene_record['refseq.protein']),
                            'P2393': gene_record['locus_tag'],
                            'P352': str(gene_record['Combined_ID']),
                            'P591': str(gene_record['EC number'])
                            }
        WD_Item_CLAIMS = {'P703': [strain_qid],
                          'P279': ['Q8054'],
                          'P680': parse_go_terms(gene_record['Gene ontology (molecular function)']),
                          'P681': parse_go_terms(gene_record['Gene ontology (cellular component)']),
                          'P682': parse_go_terms(gene_record['Gene ontology (biological process)'])
                          }
        statements = []
        # generate list of pbb core value objects for all valid claims
        for k, v in WD_Item_CLAIMS.items():
            if v is not None:
                for i in v:
                    statements.append(PBB_Core.WDItemID(value=i, prop_nr=k,
                                                        references=[uniprot_reference]))
        for k, v in WD_String_CLAIMS.items():
            if v is not None and v != 'nan':
                statements.append(PBB_Core.WDString(value=v, prop_nr=k,
                                                    references=[uniprot_reference]))
        return statements

    start = time.time()

    try:
        #find the appropriate item in wd or make a new one
        wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=protein_item_statements(),
                                                use_sparql=True)
        wd_item_protein.set_label(item_name)
        wd_item_protein.set_description(item_description, lang='en')
        wd_item_protein.set_aliases([gene_record['symbol'], gene_record['locus_tag']])
        # attempt to write json representation of item to wd
        wd_item_protein.write(login=login)

        # log the experience
        new_mgs = ''
        if wd_item_protein.create_new_item:
            new_mgs = ': New item'
        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['refseq.protein'],
            exception_type='',
            message='success{}'.format(new_mgs),
            wd_id=wd_item_protein.wd_item_id,
            duration=time.time() - start
        ))

        print('success')

    except Exception as e:
        print(e)
        PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['refseq.protein'],
            exception_type=type(e),
            message=e.__str__(),
            wd_id='',
            duration=time.time() - start
        ))
        print('no go')

    end = time.time()
    print('Time elapsed:', end - start)



