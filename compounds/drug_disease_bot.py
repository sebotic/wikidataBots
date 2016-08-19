import requests
import sys
import pandas as pd
import pprint
import json
import time
import os
import copy

import PBB_Core
import PBB_login

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'


def get_parent_molecule(ci):
    chembl_id = ci
    while True:
        all_mol_data = get_compound_data(chembl_id)
        if not all_mol_data:
            return chembl_id

        if 'molecule_hierarchy' in all_mol_data and all_mol_data['molecule_hierarchy'] \
                and 'parent_chembl_id' in all_mol_data['molecule_hierarchy']:
            parent_chembl_id = all_mol_data['molecule_hierarchy']['parent_chembl_id']
        else:
            return all_mol_data['molecule_chembl_id']

        pprint.pprint('Parent ChEMBL: {}'.format(parent_chembl_id))
        if chembl_id == parent_chembl_id:
            return parent_chembl_id
        else:
            chembl_id = parent_chembl_id

    # how to efficiently retrieve stuff beyond parent ids? Create a class?


def get_all_chembl_indications():

    all_indications = None
    next_blob = '/chembl/api/data/drug_indication.json?limit=1000&offset=0'
    while next_blob:
        print(next_blob)
        r = requests.get('https://www.ebi.ac.uk' + next_blob).json()
        next_blob = r['page_meta']['next']

        df = pd.read_json(json.dumps(r['drug_indications']))

        if all_indications is not None:
            all_indications = all_indications.append(df)
        else:
            all_indications = df

    new_index = pd.Series(data=range(0, len(all_indications.index), 1))
    all_indications.set_index(keys=new_index, inplace=True)
    # print(all_indications.index)
    # print(df.head(n=500))

    return all_indications


def get_compound_data(chembl_id):
    params = {
        'molecule_chembl_id': chembl_id,
        'format': 'json'
    }

    url = 'https://www.ebi.ac.uk/chembl/api/data/molecule'

    compound_json = requests.get(url, params=params).json()['molecules'][0]

    return compound_json


def get_id_wd_map(prop_nr):
    query = '''
        SELECT * WHERE {{
            ?qid wdt:{} ?id .
        }}
        '''.format(prop_nr)

    results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

    id_wd_map = dict()
    for z in results:
        id_wd_map[z['id']['value']] = z['qid']['value'].split('/')[-1]

    return id_wd_map


def generate_refs(ref_source_id):
    ref_list = [[]]

    if ref_source_id.startswith('C'):
        ref_list[0].extend([
            PBB_Core.WDItemID(value='Q6120337', prop_nr='P248', is_reference=True),  # stated in
            PBB_Core.WDString(value=ref_source_id, prop_nr='P592', is_reference=True),  # source element
        ])
    elif ref_source_id.startswith('N'):
        ref_list[0].extend([
            PBB_Core.WDItemID(value='Q21008030', prop_nr='P248', is_reference=True),  # stated in
            PBB_Core.WDString(value=ref_source_id, prop_nr='P2115', is_reference=True),  # source element
        ])

    ref_list[0].extend([
        PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
        # PBB_Core.WDMonolingualText(value=source_element_name, language='en',
        #                            prop_nr='P1476', is_reference=True),
        PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)  # publication date
    ])

    return ref_list


def get_ndfrt_drug_links(nui):
    url = 'https://rxnav.nlm.nih.gov/REST/Ndfrt/allInfo.json'
    params = {
        'nui': nui
    }

    results = requests.get(url=url, params=params).json()

    disease_nuis = dict()

    # make sure that only drug concepts are parsed
    if results['fullConcept']['conceptKind'] != 'DRUG_KIND':
        return disease_nuis

    try:
        results['fullConcept']['groupRoles'][0]['role']
    except TypeError:
        print(results['fullConcept']['conceptName'], 'does not have drug info')
        return disease_nuis

    for role_name in results['fullConcept']['groupRoles'][0]['role']:
        if role_name['roleName'] == 'may_treat {NDFRT}':
            disease_nui = role_name['concept'][0]['conceptNui']

            disease_results = requests.get(url, params={'nui': disease_nui}).json()

            disease_name = ''
            mesh = ''
            for disease_id in disease_results['fullConcept']['groupProperties'][0]['property']:
                if disease_id['propertyName'] == 'MeSH_Name':
                    disease_name = disease_id['propertyValue']

                if disease_id['propertyName'] == 'MeSH_DUI':
                    mesh = disease_id['propertyValue']

            print(disease_name, mesh)
            disease_nuis.update({mesh: disease_name})

    return disease_nuis


def main():
    # 'https://www.ebi.ac.uk/chembl/api/data/drug_indication/?molecule_chembl_id=CHEMBL1637&limit=100&format=json'
    # params = {
    #     'molecule_chembl_id': 'CHEMBL1637',
    #     'limit': '1000',
    #     'format': 'json'
    # }
    #
    # url = 'https://www.ebi.ac.uk/chembl/api/data/drug_indication'
    #
    # r = requests.get(url, params=params)
    # pprint.pprint(r.json())
    #
    # 'https://www.ebi.ac.uk/chembl/api/data/drug_indication.json?limit=1000&offset=0'

    # get_parent_molecule('CHEMBL2364968')

    chembl_wd_map = get_id_wd_map('P592')
    mesh_wd_map = get_id_wd_map('P486')
    ndfrt_wd_map = get_id_wd_map('P2115')
    wd_ndfrt_map = {ndfrt_wd_map[x]: x for x in ndfrt_wd_map}

    # contains drug QIDs as keys, and a dict of 'disease_qid', 'source_id' as keys. values are disease item QID and the
    # db identifier for NDF-RT or CHEMBL.

    drug_disease_map = dict()

    if os.path.isfile('drug_disease.json'):
        with open('drug_disease.json', 'r') as infile:
            drug_disease_map = json.load(infile)

    for nui in ndfrt_wd_map:
        diseases = get_ndfrt_drug_links(nui)
        drug_qid = ndfrt_wd_map[nui]
        for disease_mesh in diseases:
            if not disease_mesh:
                continue
            elif disease_mesh in mesh_wd_map:
                disease_qid = mesh_wd_map[disease_mesh]
            else:
                print('Disease not found in Wikidata:', disease_mesh, diseases[disease_mesh])
                continue

            if drug_qid in drug_disease_map:
                drug_disease_map[drug_qid]['disease_qid'].append(disease_qid)
                drug_disease_map[drug_qid]['source_id'].append(nui)
            else:
                drug_disease_map.update({
                    drug_qid: {
                        'disease_qid': [disease_qid],
                        'source_id': [nui]
                    }
                })

    # pprint.pprint(drug_disease_map)

    if os.path.isfile('full_drug_disease_map.json'):
        with open('full_drug_disease_map.json', 'r') as infile:
            drug_disease_map = json.load(infile)
    else:
        all_indications = get_all_chembl_indications()
        all_indications.to_csv('all_chembl_indications.csv', index=False)

        unique_chembl_ids = all_indications['molecule_chembl_id'].unique()
        chembl_to_parent = dict()
        unique_mesh_ids = all_indications['mesh_id'].unique()

        for chembl_id in unique_chembl_ids:
            # print('chembl id:', chembl_id)
            if chembl_id in chembl_wd_map:
                curr_chembl = chembl_id
            else:
                parent_chembl = get_parent_molecule(chembl_id)
                chembl_to_parent.update({chembl_id: parent_chembl})
                curr_chembl = parent_chembl

            if curr_chembl not in chembl_wd_map:
                print(curr_chembl, 'not found in Wikidata')
                continue

            curr_drug_qid = chembl_wd_map[curr_chembl]

            chembl_id_df = all_indications[all_indications['molecule_chembl_id'] == curr_chembl]
            # pprint.pprint(chembl_id_df)

            for x in chembl_id_df.index:
                curr_mesh = chembl_id_df.loc[x, 'mesh_id']
                # print('this current mesh', curr_mesh)
                if pd.notnull(curr_mesh) and curr_mesh in mesh_wd_map:
                    print(curr_chembl, curr_mesh, 'pair found', 'index', x)

                    disease_qid = mesh_wd_map[curr_mesh]
                    if curr_drug_qid in drug_disease_map:
                        if disease_qid not in drug_disease_map[curr_drug_qid]['disease_qid']:
                            drug_disease_map[curr_drug_qid]['disease_qid'].append(disease_qid)
                            drug_disease_map[curr_drug_qid]['source_id'].append(chembl_id)
                    else:
                        drug_disease_map.update({
                            curr_drug_qid: {
                                'disease_qid': [disease_qid],
                                'source_id': [chembl_id]
                            }
                        })

    with open('full_drug_disease_map.json', 'w') as outfile:
        json.dump(drug_disease_map, outfile)

    print(sys.argv[1])
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    for count, drug in enumerate(drug_disease_map):
        statements = list()

        for c, disease in enumerate(drug_disease_map[drug]['disease_qid']):
            ref_source_id = drug_disease_map[drug]['source_id'][c]
            references = generate_refs(ref_source_id)

            statements.append(PBB_Core.WDItemID(value=disease, prop_nr='P2175', references=references))

        try:
            item = PBB_Core.WDItemEngine(wd_item_id=drug, data=statements)
            item_qid = item.write(login)
            print('sucessfully written to', item_qid, item.get_label())
        except Exception as e:
            print('write failed to drug item:', drug)
            print(e)

        # if count > 2:
        #     break

    disease_drug_map = {z: {'drug_qid': list(), 'source_id': list()} for x in drug_disease_map
                        for z in drug_disease_map[x]['disease_qid']}

    for count, drug in enumerate(drug_disease_map):
        for c, disease in enumerate(drug_disease_map[drug]['disease_qid']):
            source = drug_disease_map[drug]['source_id'][c]
            disease_drug_map[disease]['drug_qid'].append(drug)
            disease_drug_map[disease]['source_id'].append(source)

    for count, disease in enumerate(disease_drug_map):
        statements = list()

        for c, drug in enumerate(disease_drug_map[disease]['drug_qid']):
            ref_source_id = disease_drug_map[disease]['source_id'][c]
            references = generate_refs(ref_source_id)

            statements.append(PBB_Core.WDItemID(value=drug, prop_nr='P2176', references=references))

        try:
            item = PBB_Core.WDItemEngine(wd_item_id=disease, data=statements)
            item_qid = item.write(login)
            print('sucessfully written to', item_qid, item.get_label())
        except Exception as e:
            print('write failed to disease item:', disease)
            print(e)


if __name__ == '__main__':
    sys.exit(main())
