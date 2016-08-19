import requests
import sys
import pandas as pd
import numpy as np
import pprint
import json
import time
import os
import copy

import PBB_Core
import PBB_login

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'


def get_id_wd_map(prop_nr):
    prefix = '''
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    '''

    query = '''
        SELECT * WHERE {{
            ?qid wdt:{} ?id .
        }}
        '''.format(prop_nr)

    params = {
        'query': prefix + query,
        'format': 'json'
    }

    headers = {
        'Accept': 'application/sparql-results+json'
    }

    url = 'https://query.wikidata.org/sparql'

    results = requests.get(url, params=params, headers=headers).json()['results']['bindings']

    # results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

    id_wd_map = dict()
    for z in results:
        id_wd_map[z['id']['value']] = z['qid']['value'].split('/')[-1]

    return id_wd_map


def generate_refs(iuphar_ligand):
    ref_list = [[]]

    ref_list[0].extend([
        PBB_Core.WDItemID(value='Q2793172', prop_nr='P248', is_reference=True),  # stated in
        PBB_Core.WDString(value=iuphar_ligand, prop_nr='P595', is_reference=True),  # source element
    ])

    ref_list[0].extend([
        PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
        # PBB_Core.WDMonolingualText(value=source_element_name, language='en',
        #                            prop_nr='P1476', is_reference=True),
        PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # publication date
    ])

    return ref_list


def main():
    cid_wd_map = get_id_wd_map('P662')
    uniprot_wd_map = get_id_wd_map('P352')
    # pprint.pprint(cid_wd_map)

    interaction_types = {
        'Agonist': 'Q389934',
        'Inhibitor': 'Q427492',
        'Allosteric modulator': 'Q2649417',
        'Antagonist': 'Q410943',
        'Channel blocker': 'Q5072487'

    }

    all_ligands = pd.read_csv('./iuphar_data/ligands.csv', header=0, sep=',', dtype={'PubChem CID': np.str,
                                                                                     'PubChem SID': np.str,
                                                                                     'Ligand id': np.str
                                                                                     }, low_memory=False)
    all_interactions = pd.read_csv('./iuphar_data/interactions.csv', header=0, sep=',', dtype={'ligand_id': np.str,
                                                                                               'ligand_pubchem_sid': np.str
                                                                                               }, low_memory=False)

    print(sys.argv[1])
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    for count, uniprot_id in enumerate(all_interactions['target_uniprot'].unique()):
        if uniprot_id in uniprot_wd_map:
            uniprot_id_df = all_interactions[all_interactions['target_uniprot'] == uniprot_id]

            statements = list()
            for sid in uniprot_id_df['ligand_pubchem_sid']:
                try:
                    cid = all_ligands.loc[all_ligands['PubChem SID'] == sid, 'PubChem CID'].iloc[0]
                    iuphar_ligand = all_ligands.loc[all_ligands['PubChem SID'] == sid, 'Ligand id'].iloc[0]
                    itype = uniprot_id_df.loc[uniprot_id_df['ligand_pubchem_sid'] == sid, 'type'].iloc[0]

                    qualifier = []
                    if itype in interaction_types:
                        qualifier.append(PBB_Core.WDItemID(value=interaction_types[itype], prop_nr='P366',
                                                           is_qualifier=True))

                    if cid in cid_wd_map:
                        # print(cid, 'will be added to', uniprot_id)
                        compound_qid = cid_wd_map[cid]
                        statements.append(PBB_Core.WDItemID(
                            value=compound_qid, prop_nr='P129', references=generate_refs(iuphar_ligand),
                            qualifiers=qualifier
                        ))
                except IndexError as e:
                    print('No CID found for:', sid, uniprot_id)
                    continue

            if len(statements) == 0:
                continue
            try:
                print(len(statements))
                item = PBB_Core.WDItemEngine(wd_item_id=uniprot_wd_map[uniprot_id], data=statements)
                item_qid = item.write(login)
                # pprint.pprint(item.get_wd_json_representation())
                print('sucessfully written to', item_qid, item.get_label())

            except Exception as e:
                print(e)

    for count, sid in enumerate(all_interactions['ligand_pubchem_sid'].unique()):
        try:
            cid = all_ligands.loc[all_ligands['PubChem SID'] == sid, 'PubChem CID'].iloc[0]
        except IndexError:
            continue
        if cid in cid_wd_map:
            sid_df = all_interactions[all_interactions['ligand_pubchem_sid'] == sid]

            statements = list()
            for uniprot in sid_df['target_uniprot']:
                try:
                    # cid = all_ligands.loc[all_ligands['PubChem SID'] == sid, 'PubChem CID'].iloc[0]
                    iuphar_ligand = all_ligands.loc[all_ligands['PubChem SID'] == sid, 'Ligand id'].iloc[0]
                    itype = sid_df.loc[sid_df['ligand_pubchem_sid'] == sid, 'type'].iloc[0]

                    qualifier = []
                    if itype in interaction_types:
                        qualifier.append(PBB_Core.WDItemID(value=interaction_types[itype], prop_nr='P794',
                                                           is_qualifier=True))

                    if uniprot in uniprot_wd_map:
                        # print(cid, 'will be added to', uniprot_id)
                        uniprot_qid = uniprot_wd_map[uniprot]
                        statements.append(PBB_Core.WDItemID(
                            value=uniprot_qid, prop_nr='P129', references=generate_refs(iuphar_ligand),
                            qualifiers=qualifier
                        ))
                except IndexError as e:
                    print('No Uniprot found for:', uniprot)
                    continue

            if len(statements) == 0:
                continue
            try:
                print(len(statements))
                item = PBB_Core.WDItemEngine(wd_item_id=cid_wd_map[cid], data=statements)
                item_qid = item.write(login)
                # pprint.pprint(item.get_wd_json_representation())
                print('sucessfully written to', item_qid, item.get_label())

            except Exception as e:
                print(e)

            # if count > 10:
            #     break

    # print(all_ligands.loc[all_ligands['PubChem SID'] == '178101795', 'PubChem CID'].iloc[0])
    # # print(all_ligands.head())
    #
    # count = 0
    # # pprint.pprint(all_ligands['PubChem CID'])
    # for c, compound in enumerate(all_ligands['PubChem CID']):
    #     if compound in cid_wd_map:
    #
    #         count += 1
    #         print(count, all_ligands.loc[c, 'Name'], 'cid:', compound)
    #
    # count = 0
    # for c, uniprot_id in enumerate(all_interactions['target_uniprot'].unique()):
    #     if uniprot_id in uniprot_wd_map:
    #         count += 1
    #         print(count, 'uniprot:', uniprot_id)


if __name__ == '__main__':
    sys.exit(main())