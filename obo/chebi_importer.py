import json
import PBB_login
import sys
import os

from obo_importer import OBOImporter



def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    root_objects = ['11946']

    OBOImporter.obo_synonyms = {
        'SMILES': 'P233',
        'InChIKey': 'P235',
        'FORMULA': 'P274'
    }

    file_name = 'temp_GO_onto_map.json'
    if os.path.exists(file_name):
        f = open(file_name, 'r')
        local_qid_onto_map = json.loads(f.read())
        f.close()
    else:
        local_qid_onto_map = {}

    # Ontology ref item is the Wikidata 'Gene Ontolgy' item
    OBOImporter(root_objects=root_objects, ontology='CHEBI', core_property_nr='P683',
                ontology_ref_item='Q902623', login=login, local_qid_onto_map=local_qid_onto_map)

if __name__ == '__main__':
    sys.exit(main())
