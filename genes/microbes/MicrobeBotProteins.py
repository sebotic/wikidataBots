import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import pprint
import MicrobeBotResources as MBR
import MicrobeBotWDFunctions as wdo
import pandas as pd
import time

__author__ = 'timputman'

login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])


def wd_item_construction(gene_record, spec_strain, login):
    """
    identifies and modifies or writes new wd items for proteins
    :param gene_record: pandas dataframe
    :param login: bot account login credentials
    :return: PBB_Core wd item object
    """

    def parse_go_terms(goclass):
        """
        parses the tsv formated result from uniprot REST API
        :param goclass:
        :return:
        """
        go_props = {'Function': 'P680',
                    'Component': 'P681',
                    'Process': 'P682'
                    }
        goqid = wdo.WDSparqlQueries(string=goclass[0], prop='P686').wd_prop2qid()
        return goqid, go_props[goclass[1]]

    item_name = '{}    {}'.format(gene_record['name'], gene_record['locus_tag'])
    item_description = 'microbial protein found in {}'.format(spec_strain.iloc[0]['organism_name'])
    uniprot = str(list(gene_record['uniprot'].values())[0])

    def protein_item_statements():
        """
        construct list of referenced statements to past to PBB_Core Item engine
        :return:
        """
        uniprot_ref = wdo.reference_store(source='uniprot', identifier=uniprot)

        WD_String_CLAIMS = {'P637': str(gene_record['refseq']['protein']),
                            #'P2393': gene_record['locus_tag'],
                            'P352': uniprot
                            #'P591': str(gene_record['EC number'])
                            }
        WD_Item_CLAIMS = {'P703': [spec_strain.iloc[0]['wd_qid']],
                          'P279': ['Q8054'],
                          'P680': [],  # molecular function
                          'P681': [],  # cellular component
                          'P682': []  # biological process
                          }
        for gt in gene_record['GOTERMS']:
            gtids = parse_go_terms(gt)
            WD_Item_CLAIMS[gtids[1]].append(gtids[0])

        statements = []
        # generate list of pbb core value objects for all valid claims
        for k, v in WD_Item_CLAIMS.items():
            if v:
                for i in v:
                    statements.append(PBB_Core.WDItemID(value=i, prop_nr=k, references=[uniprot_ref]))

        for k, v in WD_String_CLAIMS.items():
            if v:
                statements.append(PBB_Core.WDString(value=v, prop_nr=k, references=[uniprot_ref]))
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
            main_data_id=gene_record['refseq']['protein'],
            exception_type='',
            message='success{}'.format(new_mgs),
            wd_id=wd_item_protein.wd_item_id,
            duration=time.time() - start
        ))

        print('success')
        return 'success'

    except Exception as e:
        print(e)
        PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['refseq']['protein'],
            exception_type=type(e),
            message=e.__str__(),
            wd_id='',
            duration=time.time() - start
        ))
        print('no go')

    end = time.time()
    print('Time elapsed:', end - start)

    return protein_item_statements()
