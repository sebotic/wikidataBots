#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import time
import copy
import datetime
import zipfile
import pandas as pd
import numpy as np

import PBB_Core
from PBB_login import WDLogin

__author__ = 'Sebastian Burgstaller'
__licence__ = 'GPLv3'


class DrugBot(object):
    def __init__(self, user, pwd):
        properties = ['P279', 'P769', 'P31', 'P636', 'P267', 'P231', 'P486', 'P672', 'P662', 'P661', 'P652', 'P665', 'P683',
                      'P274', 'P715', 'P646', 'P592', 'P233', 'P234', 'P235',
                      'P18', 'P373', 'P1805', 'P657', 'P595']
        # these property names do not match those in Wikidata!!
        property_names = ['subclass of', 'significant drug interaction', 'instance of', 'route of administration', 'ATC code',
                          'CAS number', 'MeSH ID', 'MeSH Code',
                          'PubChem ID (CID)', 'ChemSpider', 'UNII', 'KEGG Drug', 'ChEBI', 'Molecular Formula', 'Drugbank ID',
                          'Freebase identifier', 'ChEMBL',
                          'SMILES', 'InChI', 'InChIKey', 'image', 'Commons category',
                          'WHO INN', 'RTECS Number', 'Guide to Pharmacology']

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

        # extract creation date of Drugbank file from Drugbank zip file
        drugbank_zip = zipfile.ZipFile('./drugbank_data/drugbank.xml.zip')
        self.drugbank_date = datetime.datetime(
            *[x for x in drugbank_zip.infolist()[0].date_time]).strftime('+%Y-%m-%dT00:00:00Z')

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
                data = []
                for col in drug_data.columns.values:
                    data_value = drug_data.loc[count, col]

                    # no values and values greater than 400 chars should not be added to wikidata.
                    if pd.isnull(data_value) or col not in name_to_prop:
                        continue
                    elif len(data_value) > 400:
                        continue

                    if col in property_names and col != 'ATC code':
                        data.append(PBB_Core.WDString(value=str(data_value).strip(), prop_nr=name_to_prop[col]))

                # add instances of (P31) of chemical compound (Q11173), pharmaceutical drug (Q12140),
                # Biologic medical product (Q679692) and  monoclonal antibodies (Q422248)
                data.append(PBB_Core.WDItemID(value='Q11173', prop_nr='P31'))
                data.append(PBB_Core.WDItemID(value='Q12140', prop_nr='P31'))

                if drug_data.loc[count, 'Drug type'] == 'biotech':
                    data.append(PBB_Core.WDItemID(value='Q679692', prop_nr='P31'))

                if drug_data.loc[count, 'Name'][-3:] == 'mab':
                    data.append(PBB_Core.WDItemID(value='Q422248', prop_nr='P31'))

                # for instance of, do not overwrite what other users have put there
                append_value = ['P31']

                # split the ATC code values present as one string in the csv file
                if pd.notnull(drug_data.loc[count, 'ATC code']):
                    for atc in drug_data.loc[count, 'ATC code'].split(';'):
                        data.append(PBB_Core.WDString(value=atc, prop_nr='P267'))


                drugbank_ref = [[
                        PBB_Core.WDItemID(value='Q1122544', prop_nr='P248', is_reference=True),
                        PBB_Core.WDString(value=drug_data.loc[count, 'Drugbank ID'], prop_nr='P715', is_reference=True),
                        PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),
                        PBB_Core.WDMonolingualText(value=drug_data.loc[count, 'Name'], language='en',
                                                   prop_nr='P1476', is_reference=True)
                    ], [
                        PBB_Core.WDTime(time=self.drugbank_date, prop_nr='P577', is_reference=True)  # publication date
                    ]]

                drugbank_source = ['instance of', 'ATC code', 'CAS number', 'Drugbank ID', 'Molecular Formula',  'InChI', 'InChIKey']
                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in drugbank_source]:
                        i.set_references(copy.deepcopy(drugbank_ref))

                chembl_ref = [[
                        PBB_Core.WDItemID(value='Q6120337', prop_nr='P248', is_reference=True),  # stated in
                        PBB_Core.WDString(value=drug_data.loc[count, 'ChEMBL'], prop_nr='P592', is_reference=True),  # source element
                        PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of database
                        PBB_Core.WDMonolingualText(value=drug_data.loc[count, 'Name'], language='en',
                                                   prop_nr='P1476', is_reference=True)  # title of source DB entry
                    ], [
                        PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)
                    ]]

                chembl_source = ['ChEMBL', 'ChemSpider', 'KEGG Drug', 'ChEBI', 'SMILES', 'WHO INN', 'Guide to Pharmacology']
                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in chembl_source]:
                        i.set_references(copy.deepcopy(chembl_ref))

                pubchem_ref = [[
                        PBB_Core.WDItemID(value='Q6120337', prop_nr='P248', is_reference=True),  # stated in
                        PBB_Core.WDString(value=drug_data.loc[count, 'PubChem ID (CID)'], prop_nr='P592', is_reference=True),  # source element
                        PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of database
                        PBB_Core.WDMonolingualText(value=drug_data.loc[count, 'Name'], language='en',
                                                   prop_nr='P1476', is_reference=True)  # title of source DB entry
                    ], [
                        PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z'), prop_nr='P813', is_reference=True)
                    ]]

                pubchem_source = ['MeSH ID', 'PubChem ID (CID)', 'UNII']
                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in pubchem_source] and pd.notnull(drug_data.loc[count, 'PubChem ID (CID)']):
                        i.set_references(copy.deepcopy(pubchem_ref))

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

                    wd_item = PBB_Core.WDItemEngine(item_name=label, domain=domain, data=data,
                                                    server='www.wikidata.org', append_value=append_value)

                    # overwrite only certain descriptions
                    descriptions_to_overwrite = {'chemical compound', 'chemical substance', ''}
                    if wd_item.get_description() in descriptions_to_overwrite:
                        wd_item.set_description(description='pharmaceutical drug', lang='en')

                    wd_item.set_label(label=label, lang='en')

                    if pd.notnull(drug_data.loc[count, 'Aliases']):
                        wd_item.set_aliases(aliases=aliases, lang='en', append=True)

                    pprint.pprint(wd_item.get_wd_json_representation())

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

                if count == 2:
                    break
