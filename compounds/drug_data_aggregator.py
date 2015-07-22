#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'sebastian'

"""extract relevant data from the drugbank.ca database xml file and put it into a CSV file"""


import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import os
import requests
import zipfile
import simplejson


def convert_to_index_numbers(formula_string):
    """
    Converts the numbers in a normal string into unicode index numbers (as used in chemical formulas)
    :param formula_string: a string containing numbers which should be converted to index numbers
    :type formula_string: str
    :return: returns a unicode string with numbers converted to index numbers
    """
    index_numbers = [u'₀', u'₁', u'₂', u'₃', u'₄', u'₅', u'₆', u'₇', u'₈', u'₉']
    conventional_numbers = [u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9']

    conversion_map = dict(zip(conventional_numbers, index_numbers))

    for i in set(formula_string):
        if i in conversion_map:
            formula_string = formula_string.replace(i, conversion_map[i])

    return(formula_string)

def rest_query(url, params=dict()):
    """
    Executes a query to a REST API and returns the result
    :param url: A URL to the REST service
    :type url: str
    :param params: a dictionary with parameters passed to the REST API, will then be formated as a proper URL by requests
    :type params: dict
    :return: a Python json representation dict object of the server reply
    """
    # the accept header is required for the PubChem RDF REST API,
    # otherwise an internal server error will be triggered (HTTP response code 500)!!!
    headers = {'accept': 'text/html,text/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    try:
        reply = requests.get(url, params=params, headers=headers)
        print(reply.url)

        if reply.status_code == 404:
            return({})
        else:
            return(reply.json())

    except requests.HTTPError as e:
        print(e)
        return({})
    except simplejson.JSONDecodeError as e:
        print(e)
        return({})


drugbank_headers = [
    'Drugbank ID', 'Name', 'Secondary ID',
    'Tertiary ID', 'Drug type', 'Status',
    'CAS number', 'KEGG Drug',
    'National Drug Code Directory', 'PharmGKB', 'UniProtKB',
    'Wikipedia', 'ChEMBL', 'ChEBI',
    'InChI', 'InChIKey', 'SMILES', 'Molecular Formula', 'Guide to Pharmacology', 'Aliases', 'WHO INN',
    'ATC code', 'NDF-RT NUI', 'UNII', 'PubChem ID (CID)', 'MeSH ID'
]

# append tells the program to append to an existing .csv file
append = True

# check if an appropriate CSV file exists or create new file
if os.path.isfile('./drugbank_data/drugbank.csv') and append:
    drugbank_data = pd.read_csv('./drugbank_data/drugbank.csv', index_col=0, dtype={'PubChem ID (CID)': str,
                                                                                        'ChEBI': str,
                                                                                        'ChEMBL': str
                                                                                        })
    drugbank_data['PubChem ID (CID)'] = drugbank_data.loc[drugbank_data['PubChem ID (CID)'].map(
        lambda x: pd.notnull(x)), 'PubChem ID (CID)'].map(lambda x: x.split('.')[0])
    drugbank_data['ChEBI'] = drugbank_data.loc[drugbank_data['ChEBI'].map(
        lambda x: pd.notnull(x)), 'ChEBI'].map(lambda x: x.split('.')[0])
else:
    drugbank_data = pd.DataFrame(columns=drugbank_headers, dtype=object)


# download and extract drugbank xml file
url = 'http://www.drugbank.ca/system/downloads/current/drugbank.xml.zip'
drugbank_file = './drugbank_data/drugbank.xml.zip'
reply = requests.get(url, stream=True)
with open(drugbank_file, 'wb') as f:
    for chunk in reply.iter_content(chunk_size=2048):
        if chunk:
            f.write(chunk)
            f.flush()

db_zip = open(drugbank_file, 'rb')
zipfile.ZipFile(db_zip).extract('drugbank.xml', './drugbank_data/')
db_zip.close()

f = open('./drugbank_data/drugbank.xml', 'r')
print(drugbank_data.dtypes)
# tree = ET.parse(f)
# drugbank_root = tree.getroot()

count = 0
for event, e in ET.iterparse(f, events=('start', 'end')):
    if event == 'end' and e.tag == '{http://www.drugbank.ca}drug' and 'type' in e.attrib:

        drugbank_data.loc[count, 'Drug type'] = e.attrib['type']
        # print(start_element.attrib['type'])
        drugbank_ids = e.findall('./{http://www.drugbank.ca}drugbank-id')

        # skip existing data rows
        if drugbank_ids[0].text in drugbank_data['Drugbank ID'].values and append:
            if not count > drugbank_data['Drugbank ID'].index.max():
                print('Skipping:', drugbank_data.loc[count, 'Name'], 'aready in table')
                count += 1
                e.clear()
                continue
            else:
                break

        drugbank_data.loc[count, 'Drugbank ID'] = drugbank_ids[0].text

        if len(drugbank_ids) >= 2:
            drugbank_data.loc[count, 'Secondary ID'] = drugbank_ids[1].text
        if len(drugbank_ids) >= 3:
            drugbank_data.loc[count, 'Tertiary ID'] = drugbank_ids[2].text

        for drugbank_group in e.findall('./{http://www.drugbank.ca}groups/{http://www.drugbank.ca}group'):
            if drugbank_group.text == 'approved':
                drugbank_data.loc[count, 'Status'] = 'approved'
            elif drugbank_group.text == 'withdrawn':
                drugbank_data.loc[count, 'Status'] = 'withdrawn'

        drugbank_data.loc[count, 'Name'] = e.findall('./{http://www.drugbank.ca}name')[0].text
        drugbank_data.loc[count, 'CAS number'] = e.findall('./{http://www.drugbank.ca}cas-number')[0].text

        for prop in e.findall('./{http://www.drugbank.ca}calculated-properties/{http://www.drugbank.ca}property'):
            kind = prop.find('./{http://www.drugbank.ca}kind').text
            value = prop.find('./{http://www.drugbank.ca}value').text

            if kind in drugbank_headers:
                drugbank_data.loc[count, kind] = value

        for eid in e.findall('./{http://www.drugbank.ca}external-identifiers/{http://www.drugbank.ca}external-identifier'):
            id_name = eid.find('./{http://www.drugbank.ca}resource').text
            id_value = eid.find('./{http://www.drugbank.ca}identifier').text

            if id_name in drugbank_headers:
                drugbank_data.loc[count, id_name] = id_value

        # read ATC codes
        atc_codes = set()
        for atc_code in e.findall('./{http://www.drugbank.ca}atc-codes/{http://www.drugbank.ca}atc-code'):
            atc_codes.add(atc_code.attrib['code'])

        drugbank_data.loc[count, 'ATC code'] = u';'.join(atc_codes)

        # read aliases and WHO INN unique compound name
        aliases = set()
        for synonym in e.findall('./{http://www.drugbank.ca}synonyms/{http://www.drugbank.ca}synonym'):
            if synonym.attrib['coder'] == 'INN, BAN, USAN':
                drugbank_data.loc[count, 'WHO INN'] = synonym.text
                continue

            if synonym.attrib['language'] == '':
                aliases.add(synonym.text)

        drugbank_data.loc[count, 'Aliases'] = u';'.join(aliases)

        print(drugbank_data.loc[count, 'Name'])

        # retrieve NUI and UNII from NDF-RT
        nui = np.NaN
        unii = np.NaN

        params = {
            'conceptName': drugbank_data.loc[count, 'Name'],
            'kindName': 'DRUG_KIND'
        }

        ndfrt_reply = rest_query('https://rxnav.nlm.nih.gov/REST/Ndfrt/search.json', params=params)

        if ndfrt_reply['groupConcepts'][0] is not None:
            nui = ndfrt_reply['groupConcepts'][0]['concept'][0]['conceptNui']

            unii_search_params = {
                'nui': nui,
                'propertyName': 'FDA_UNII'
            }
            ndfrt_reply = rest_query('https://rxnav.nlm.nih.gov/REST/Ndfrt/properties.json', params=unii_search_params)
            if ndfrt_reply['groupProperties'][0] is not None:
                unii = ndfrt_reply['groupProperties'][0]['property'][0]['propertyValue']

        drugbank_data.loc[count, 'NDF-RT NUI'] = nui
        drugbank_data.loc[count, 'UNII'] = unii

        # get PubChem ID and MeSH ID from PubChem by querying with InChIKey
        cid = np.NaN
        mesh_id = np.NaN
        inchi_key = drugbank_data.loc[count, 'InChIKey']

        if pd.notnull(inchi_key):
            inchi_key = inchi_key[9:]
            pubchem_reply = rest_query('https://pubchem.ncbi.nlm.nih.gov/rest/rdf/inchikey/{}.json'.format(inchi_key))
            if len(pubchem_reply) > 0:
                for key, value in pubchem_reply['inchikey/{}'.format(inchi_key)].items():
                    print(key, value)
                    if key == u'http://semanticscience.org/resource/is-attribute-of':
                        cid = value[0]['value'][12:]
                        print('cid:', cid)

                    if key == u'http://purl.org/dc/terms/subject':
                        mesh_id = value[0]['value'][27:]
                        print('MeSH ID:', mesh_id)

        drugbank_data.loc[count, 'PubChem ID (CID)'] = cid
        drugbank_data.loc[count, 'MeSH ID'] = mesh_id

        if count % 100 == 0:
            drugbank_data.to_csv('./drugbank_data/drugbank.csv', index=True, encoding='utf-8', header=True)
            print('count:', count)

        count += 1
        e.clear()

# convert molecular formular numbers to small utf-8 index numbers
drugbank_data['Molecular Formula'] = drugbank_data.loc[drugbank_data['Molecular Formula'].map(lambda x: pd.notnull(x)),
                                                       'Molecular Formula'].map(lambda x: convert_to_index_numbers(x))

drugbank_data.to_csv('./drugbank_data/drugbank.csv', index=True, encoding='utf-8', header=True)