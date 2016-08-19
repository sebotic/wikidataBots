import requests
import sys
import pandas as pd
import pprint
import json
import time
import copy

import PBB_Core


def get_entrez_qid_map(prop_nr):
    query = '''
        SELECT * WHERE {{
            ?qid wdt:{} ?id .
            ?qid wdt:P703 wd:Q5 .
        }}
        '''.format(prop_nr)

    results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

    id_wd_map = dict()
    for z in results:
        id_wd_map[z['id']['value']] = z['qid']['value'].split('/')[-1]

    return id_wd_map


def main():
    # mirtar_base = pd.read_excel('~/Downloads/hsa_MTI(2).xlsx')
    mirtar_base = pd.read_csv('~/Downloads/hsa_MTI.csv', header=0, sep=',')
    pprint.pprint(mirtar_base.head(2))

    pprint.pprint(mirtar_base.iloc[1, 0])
    # pprint.pprint(mirtar_base.index)

    entrez_qid_map = get_entrez_qid_map('P351')

    # create subclass of 'mature microRNA'
    # create encoded by (if this can be determined, would be important)
    # create 'encodes' property on the genes
    # create 'found in taxon' property

    unique_mirs = mirtar_base['molecule_chembl_id'].unique()

    for mir in unique_mirs:

        # references = generate_refs(chembl_id)

        curr_mir_df = unique_mirs[unique_mirs['miRNA'] == mir]

        statements = list()

        # mature miRNA Q23838648

        for x in curr_mir_df.index:
            curr_mesh = curr_mir_df.loc[x, 'mesh_id']
            if pd.notnull(curr_mesh) and curr_mesh in mesh_wd_map:
                print(chembl_id, curr_mesh, 'found')



if __name__ == '__main__':
    sys.exit(main())