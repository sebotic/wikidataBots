#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Sebastian Burgstaller'
__licence__ = 'GPLv3'

import os
import time
import copy
import logging
import pandas as pd
import numpy as np

import PBB_Core
from PBB_login import WDLogin


class DrugBot(object):
    def __init__(self, user, pwd):
        properties = ['P279', 'P769', 'P31', 'P636', 'P267', 'P231', 'P486', 'P672', 'P662', 'P661', 'P652', 'P665', 'P683',
                      'P274', 'P715', 'P646', 'P592', 'P233', 'P234', 'P235',
                      'P18', 'P373', 'P1805', 'P657']
        # these property names do not match those in Wikidata!!
        property_names = ['subclass of', 'significant drug interaction', 'instance of', 'route of administration', 'ATC code',
                          'CAS number', 'MeSH ID', 'MeSH Code',
                          'PubChem ID (CID)', 'ChemSpider', 'UNII', 'KEGG Drug', 'ChEBI', 'Molecular Formula', 'Drugbank ID',
                          'Freebase identifier', 'ChEMBL',
                          'SMILES', 'InChI', 'InChIKey', 'image', 'Commons category',
                          'WHO INN', 'RTECS Number']

        prop_to_name = dict(zip(properties, property_names))
        name_to_prop = dict(zip(property_names, properties))

        login_obj = WDLogin(user=user, pwd=pwd, server='www.wikidata.org')

        drug_data = pd.read_csv('./drugbank_data/drugbank.csv', index_col=0, engine='c', encoding='utf-8',
                                dtype={'PubChem ID (CID)': np.str,
                                       'ChEBI': np.str,
                                       'ChEMBL': np.str,
                                       'ChemSpider': np.str,
                                       'Guide to Pharmacology': np.str
                                       })

        # log_file_col_names = ['Drugbank ID', 'time', 'Exception type', 'message' 'WD QID', 'duration']
        # self.logfile = pd.DataFrame(columns=log_file_col_names, dtype=object)
        #
        # if not os.path.exists('./logs'):
        #     os.makedirs('./logs')

        print(drug_data.dtypes)

        base_ref = {
            'ref_properties': ['P248'],
            'ref_values': ['Q1122544']
        }

        # remove potential 'InChI=' and 'InChIKey=' prefixes
        for i in drug_data['InChI'].index:
            if pd.notnull(drug_data['InChI'].at[i]):
                if 'InChI=' in drug_data['InChI'].at[i]:
                    drug_data['InChI'].at[i] = drug_data['InChI'].at[i][6:]
                if 'InChIKey=' in drug_data['InChIKey'].at[i]:
                    drug_data['InChIKey'].at[i] = drug_data['InChIKey'].at[i][9:]

        # remove DB prefix from Drugbank ID (should be corrected in the Wikidata property)
        for i in drug_data['Drugbank ID'].index:
            if pd.notnull(drug_data['Drugbank ID'].at[i]):
                drug_data['Drugbank ID'].at[i] = drug_data['Drugbank ID'].at[i][2:]

        # Iterate though all drugbank compounds and add those to Wikidata which are either FDA-approved or have been
        # withdrawn from the market. Add all non-missing values for each drug to Wikidata.
        for count in drug_data.index:
            print('Count is:', count)

            if drug_data.loc[count, 'Status'] == 'approved' or drug_data.loc[count, 'Status'] == 'withdrawn':
                data = {}
                references = {}
                for col in drug_data.columns.values:
                    data_value = drug_data.loc[count, col]

                    # no values and values greater than 400 chars should not be added to wikidata.
                    if pd.isnull(data_value) or col not in name_to_prop:
                        continue
                    elif len(data_value) > 400:
                        continue

                    if col in property_names:
                        data.update({name_to_prop[col]: [str(data_value).strip()]})
                        references.update({name_to_prop[col]: [copy.deepcopy(base_ref)]})

                # add instances of (P31) of chemical compound (Q11173) and pharmaceutical drug (Q12140)
                # TODO: add Biologic medical product (Q679692) and  monoclonal antibodies (Q422248) as instances
                data.update({
                    'P31': ['Q11173', 'Q12140']
                })

                # for instance of, do not overwrite what other users have put there
                append_value = ['P31']

                # split the ATC code values present as one string in the csv file
                if 'P267' in data:
                    data.update({
                        'P267': drug_data.loc[count, 'ATC code'].split(';')
                    })
                    references.update({
                        'P267': [copy.deepcopy(base_ref) for x in data['P267']]
                    })

                # add PubChem ref for PubChem CID
                if 'P662' in references:
                    references['P662'] = [{
                        'ref_properties': ['P248'],
                        'ref_values': ['Q278487']
                    }]

                # add PubChem ref for MeSH ID
                if 'P486' in references:
                    references['P486'] = [{
                        'ref_properties': ['P248'],
                        'ref_values': ['Q278487']
                    }]

                label = drug_data.loc[count, 'Name']
                domain = 'drugs'

                # If label in aliases list, remove the label from it. If an alias is longer than 250 chars, also remove
                # Aliases longer than 250 characters will trigger an WD API error.
                if pd.notnull(drug_data.loc[count, 'Aliases']):
                    aliases = drug_data.loc[count, 'Aliases'].split(';')
                    for i in aliases:
                        if i == label or i == label.lower() or len(i) > 250:
                            aliases.remove(i)

                start = time.time()

                # pprint.pprint(data)
                # pprint.pprint(references)
                print('Drug name:', label)
                try:

                    wd_item = PBB_Core.WDItemEngine(item_name=label, domain=domain, data=data, server='www.wikidata.org',
                                                    append_value=append_value, references=references)

                    # overwrite only certain descriptions
                    descriptions_to_overwrite = {'chemical compound', 'chemical substance', ''}
                    if wd_item.get_description() in descriptions_to_overwrite:
                        wd_item.set_description(description='pharmaceutical drug', lang='en')

                    wd_item.set_label(label=label, lang='en')

                    if pd.notnull(drug_data.loc[count, 'Aliases']):
                        wd_item.set_aliases(aliases=aliases, lang='en', append=True)

                    # pprint.pprint(wd_item.get_wd_json_representation())

                    wd_item.write(login_obj)

                    new_mgs = ''
                    if wd_item.create_new_item:
                        new_mgs = ': New item'

                    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=drug_data['Drugbank ID'].at[count],
                        exception_type='',
                        message='success{}'.format(new_mgs),
                        wd_id=wd_item.wd_item_id,
                        duration=time.time() - start
                    ))

                except Exception as e:
                    print(e)

                    PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=drug_data['Drugbank ID'].at[count],
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))

                end = time.time()
                print('Time elapsed:', end - start)
