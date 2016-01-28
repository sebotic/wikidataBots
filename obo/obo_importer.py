import PBB_Core
import PBB_login
import sys
import time
import urllib
import requests
import pprint

__author__ = 'Sebastian Burgstaller'
__license__ = 'AGPLv3'

"""

relevant Wikidata items:
entity|thing|owl:Thing Q35120
part of
has part
"""


class OBOImporter(object):
    obo_wd_map = {'http://www.w3.org/2000/01/rdf-schema#subClassOf': 'P279',  # subclassOf aka 'is a'
                  'http://purl.obolibrary.org/obo/BFO_0000051': 'P257',  # has_part
                  'http://purl.obolibrary.org/obo/BFO_0000050': 'P361'  # part of
                  }

    def __init__(self, root_objects, ontology, core_property_nr, login):

        # run go prefix fixer before any attempts to make new go terms!
        self.login_obj = login
        self.root_objects = root_objects
        self.core_property_nr = core_property_nr
        self.ontology = ontology
        self.base_url = 'http://www.ebi.ac.uk/ols/beta/api/ontologies/{}/terms/'.format(ontology)
        self.base_url += 'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F'

        self.headers = {
            'Accept': 'application/json'
        }

        for ro in root_objects:
            try:
                r = requests.get(url=self.base_url + '{}_{}/graph'.format(self.ontology, ro), headers=self.headers)
            except requests.HTTPError as e:
                print(e)
                continue

            print(r.url)
            self.term_graph = r.json()
            pprint.pprint(self.term_graph)

            children = []
            parents = []
            part_of = []
            has_part = []
            for edge in self.term_graph['edges']:
                if edge['label'] == 'is a':
                    graph_source = edge['source'].split('_')[1]
                    if graph_source == ro:
                        parents.append(graph_source)
                    else:
                        children.append(graph_source)

            self.write_term(current_root_id=ro, parents=parents, children=children)
            OBOImporter(root_objects=children, ontology=ontology, login=login)

    def write_term(self, current_root_id, parents, children):

        def get_item_qid(go_id, data=()):
            try:
                data = list(data)
                r = requests.get(url=self.base_url + '{}_{}'.format(self.ontology, go_id), headers=self.headers)
                go_term_data = r.json()
                label = go_term_data['label']
                description = go_term_data['description'][0]
                aliases = go_term_data['synonyms']

                # get parent GO term info so item can be populated with description, etc.
                data.append([PBB_Core.WDString(value='GO:{}'.format(go_id), prop_nr=self.core_property_nr)])
                wd_item = PBB_Core.WDItemEngine(item_name='test', domain='obo', data=data, use_sparql=True)
                wd_item.set_label(label=label)
                if len(description) <= 250:
                    wd_item.set_description(description=description)
                wd_item.set_aliases(aliases=aliases)
                wd_item.write(login=self.login_obj)
                return wd_item.wd_item_id
            except Exception as e:
                print(e)
                # TODO: Logging should go here
                return None

        parent_qids = []
        for parent_id in parents:
            pi = get_item_qid(parent_id)
            if pi is not None:
                parent_qids.append(pi)

        for edge in self.term_graph:
            if edge['uri'] in self.obo_wd_map:
                prop_nr = self.obo_wd_map[edge['uri']]

        pass

    def create_reference(self):
        pass


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    #  cellular component (Q5058355)

    prefix = 'GO_'
    # biological process (GO:0008150), molecular function (GO:0003674), cellular component (GO:0005575)
    root_objects = ['0008150', '0003674', '0005575']
    root_objects = ['0001218']

    OBOImporter(root_objects=root_objects, ontology='GO', core_property_nr='P686', login=login)


if __name__ == '__main__':
    sys.exit(main())
