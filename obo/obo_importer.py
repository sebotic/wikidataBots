import PBB_Core
import PBB_login
import sys
import time
import requests
import pprint
import json
import os
import traceback

__author__ = 'Sebastian Burgstaller'
__license__ = 'AGPLv3'

"""

relevant Wikidata items:
entity|thing|owl:Thing Q35120
part of
has part
"""


class OBOImporter(object):
    obo_wd_map = {
        'http://www.w3.org/2000/01/rdf-schema#subClassOf': {'P279': ''},  # subclassOf aka 'is a'
        'http://purl.obolibrary.org/obo/BFO_0000051': {'P527': ''},  # has_part
        'http://purl.obolibrary.org/obo/BFO_0000050': {'P361': ''},  # part of

        'http://purl.obolibrary.org/obo/RO_0002211': {'P128': ''},  # regulates
        'http://purl.obolibrary.org/obo/RO_0002212': {'P128': {'P794': 'Q22260640'}},  # negatively regulates WD item: Q22260640
        'http://purl.obolibrary.org/obo/RO_0002213': {'P128': {'P794': 'Q22260639'}},  # positively regulates WD item: Q22260639
    }

    rev_prop_map = {
        'http://purl.obolibrary.org/obo/BFO_0000051': 'http://purl.obolibrary.org/obo/BFO_0000050',
        'http://purl.obolibrary.org/obo/BFO_0000050': 'http://purl.obolibrary.org/obo/BFO_0000051'
    }

    xref_props = {
        'UBERON': 'P1554',
        'MSH': 'P486',
        'NCI': 'P1748',  # NCI thesaurus, there exists a second NCI property
        'CHEBI': 'P683',
        'OMIM': 'P492',
        'EC': 'P591',
    }

    ols_session = requests.Session()

    def __init__(self, root_objects, ontology, core_property_nr, ontology_ref_item, login, local_qid_onto_map):

        # run go prefix fixer before any attempts to make new go terms!
        self.login_obj = login
        self.root_objects = root_objects
        self.core_property_nr = core_property_nr
        self.ontology = ontology
        self.ontology_ref_item = ontology_ref_item
        self.base_url = 'http://www.ebi.ac.uk/ols/beta/api/ontologies/{}/terms/'.format(ontology)
        self.base_url += 'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F'

        self.headers = {
            'Accept': 'application/json'
        }

        # as SPARQL endpoint updates are not fast enough, a local temporary mapping is required
        self.local_qid_onto_map = local_qid_onto_map
        # pprint.pprint(self.local_qid_onto_map)

        for ro in root_objects:
            if ro in self.local_qid_onto_map and self.local_qid_onto_map[ro]['had_root_write'] and \
                    ('children' in self.local_qid_onto_map[ro] or 'parents' in self.local_qid_onto_map[ro]):

                OBOImporter(root_objects=self.local_qid_onto_map[ro]['children'], ontology=ontology,
                            core_property_nr=self.core_property_nr, ontology_ref_item=self.ontology_ref_item,
                            login=login, local_qid_onto_map=self.local_qid_onto_map)
            else:
                try:
                    r = OBOImporter.ols_session.get(url=self.base_url + '{}_{}/graph'.format(self.ontology, ro), headers=self.headers)
                    self.term_graph = r.json()
                except requests.HTTPError as e:
                    print(e)
                    continue
                except ValueError as e:
                    print(e)
                    continue

                print(r.url)
                pprint.pprint(self.term_graph)

                children = []
                parents = []
                for edge in self.term_graph['edges']:
                    if edge['label'] == 'is a':
                        # only accept terms from a certain ontology, ignore other (OWL) targets.
                        if len(edge['source'].split('_')) > 1:
                            graph_source = edge['source'].split('_')[1]
                        else:
                            continue

                        if graph_source == ro:
                            if len(edge['target'].split('_')) > 1:
                                parents.append(edge['target'].split('_')[1])
                            else:
                                continue
                        else:
                            children.append(graph_source)

                self.write_term(current_root_id=ro, parents=set(parents), children=set(children))

                OBOImporter(root_objects=children, ontology=ontology, core_property_nr=self.core_property_nr,
                            ontology_ref_item=self.ontology_ref_item, login=login,
                            local_qid_onto_map=self.local_qid_onto_map)

    def write_term(self, current_root_id, parents, children):
        print('current_root', current_root_id, parents, children)
        current_node_qids = []

        def get_item_qid(go_id, data=()):
            start = time.time()

            # for efficiency reasons, skip if item already had a root write performed
            if go_id in self.local_qid_onto_map and self.local_qid_onto_map[go_id]['had_root_write'] \
                    and 'qid' in self.local_qid_onto_map[go_id]:
                return self.local_qid_onto_map[go_id]['qid'], False, False

            try:
                data = list(data)

                r = OBOImporter.ols_session.get(url=self.base_url + '{}_{}'.format(self.ontology, go_id),
                                                headers=self.headers)
                go_term_data = r.json()
                label = go_term_data['label']
                description = go_term_data['description'][0]

                if go_term_data['is_obsolete']:
                    OBOImporter.cleanup_obsolete_edges(ontology_id='{}:{}'.format(self.ontology, go_id),
                                                       login=self.login_obj, core_property_nr=self.core_property_nr,
                                                       obsolete_term=True)
                    return None, None, None

                # get parent ontology term info so item can be populated with description, etc.
                data.append(PBB_Core.WDString(value='GO:{}'.format(go_id), prop_nr=self.core_property_nr,
                                              references=[self.create_reference()]))

                # add xrefs
                if go_term_data['obo_xref']:
                    for xref in go_term_data['obo_xref']:
                        if xref['database'] in OBOImporter.xref_props:
                            if xref['database'] in OBOImporter.xref_props:
                                wd_prop = OBOImporter.xref_props[xref['database']]
                            else:
                                continue
                            xref_value = xref['id']
                            data.append(PBB_Core.WDExternalID(value=xref_value, prop_nr=wd_prop,
                                                              references=[self.create_reference()]))

                if go_id in self.local_qid_onto_map:
                    wd_item = PBB_Core.WDItemEngine(wd_item_id=self.local_qid_onto_map[go_id]['qid'], domain='obo',
                                                    data=data, fast_run=True, fast_run_base_filter={'P686': ''})
                else:
                    wd_item = PBB_Core.WDItemEngine(item_name='test', domain='obo', data=data, fast_run=True,
                                                    fast_run_base_filter={'P686': ''})
                wd_item.set_label(label=label)
                if len(description) <= 250:
                    wd_item.set_description(description=description)
                else:
                    wd_item.set_description(description='Gene Ontology term')
                if go_term_data['synonyms'] is not None and len(go_term_data['synonyms']) > 0:
                    aliases = []
                    for alias in go_term_data['synonyms']:
                        if len(alias) <= 250:
                            aliases.append(alias)

                    wd_item.set_aliases(aliases=aliases)

                new_msg = ''
                if wd_item.create_new_item:
                    new_msg = ': created new GO term'

                qid = wd_item.write(login=self.login_obj)

                if go_id not in self.local_qid_onto_map:
                    self.local_qid_onto_map[go_id] = {
                        'qid': qid,
                        'had_root_write': False,
                    }

                if go_id == current_root_id:
                    self.local_qid_onto_map[go_id]['had_root_write'] = True
                    self.local_qid_onto_map[go_id]['parents'] = list(parents)
                    self.local_qid_onto_map[go_id]['children'] = list(children)

                current_node_qids.append(qid)
                print('QID created or retrieved', qid)

                PBB_Core.WDItemEngine.log(
                    'INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}:{}'.format(self.ontology, go_id),
                            exception_type='',
                            message='success{}'.format(new_msg),
                            wd_id=qid,
                            duration=time.time() - start
                        ))
                return qid, go_term_data['obo_xref'], wd_item.require_write

            except Exception as e:
                print(e)
                # traceback.print_exc(e)

                PBB_Core.WDItemEngine.log(
                    'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}:{}'.format(self.ontology, go_id),
                            exception_type=type(e),
                            message=e.__str__(),
                            wd_id='',
                            duration=time.time() - start
                        ))
                return None, None, None

        dt = []
        parent_qids = []
        write_reqired = []
        for parent_id in parents:
            pi, o, w = get_item_qid(parent_id)
            write_reqired.append(w)

            if pi:
                parent_qids.append(pi)
                dt.append(PBB_Core.WDItemID(value=pi, prop_nr='P279', references=[self.create_reference()]))

        for edge in self.term_graph['edges']:
            if edge['uri'] in self.obo_wd_map and edge['uri'] != 'http://www.w3.org/2000/01/rdf-schema#subClassOf':
                go = edge['target'].split('_')[-1]
                if go != current_root_id:
                    xref_dict = self.obo_wd_map[edge['uri']]
                elif edge['uri'] in self.rev_prop_map and edge['source'].split('_')[-1] != current_root_id:
                    xref_dict = self.obo_wd_map[self.rev_prop_map[edge['uri']]]
                    go = edge['source'].split('_')[-1]
                else:
                    continue

                pi, o, w = get_item_qid(go_id=go)
                write_reqired.append(w)
                dt.append(self.create_xref_statement(value=pi, xref_dict=xref_dict))

        root_qid, obsolete, w = get_item_qid(go_id=current_root_id, data=dt)
        if obsolete and not any(write_reqired):
            OBOImporter.cleanup_obsolete_edges(ontology_id='{}:{}'.format(self.ontology, current_root_id),
                                               login=self.login_obj, core_property_nr=self.core_property_nr,
                                               current_node_qids=current_node_qids)

        print('----COUNT----:', len(self.local_qid_onto_map))
        f = open('temp_{}_onto_map.json'.format(self.ontology), 'w')
        f.write(json.dumps(self.local_qid_onto_map))
        f.close()

    def create_reference(self):
        refs = [
            PBB_Core.WDItemID(value=self.ontology_ref_item, prop_nr='P248', is_reference=True),
            PBB_Core.WDItemID(value='Q22230760', prop_nr='P143', is_reference=True),
            PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z', time.gmtime()), prop_nr='P813',
                            is_reference=True),
            PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
        ]
        refs[0].overwrite_references = True

        return refs

    def create_xref_statement(self, value, xref_dict):
        for prop_nr, v in xref_dict.items():
            qualifiers = []
            if v:
                for p, vv in v.items():
                    qualifiers.append(PBB_Core.WDItemID(value=vv, prop_nr=p, is_qualifier=True))

            return PBB_Core.WDItemID(value=value, prop_nr=prop_nr, qualifiers=qualifiers,
                                     references=[self.create_reference()])

    @staticmethod
    def cleanup_obsolete_edges(ontology_id, core_property_nr, login, current_node_qids=(), obsolete_term=False):
        filter_props_string = ''
        if not obsolete_term:
            for x in OBOImporter.obo_wd_map.values():
                prop_nr = list(x.keys())[0]
                filter_props_string += 'Filter (?p = wdt:{})\n'.format(prop_nr)

        query = '''
        SELECT DISTINCT ?qid ?p ?onto_qid WHERE {{
            {{
                SELECT DISTINCT ?onto_qid WHERE {{
                    ?onto_qid wdt:{2} '{0}' .
                }}
            }}
            ?qid ?p [wdt:{2} '{0}'].
            {1}
        }}
        ORDER BY ?qid
        '''.format(ontology_id, filter_props_string, core_property_nr)
        print(query)

        sr = PBB_Core.WDItemEngine.execute_sparql_query(query=query)

        for occurrence in sr['results']['bindings']:
            if 'statement' in occurrence['qid']['value']:
                continue

            start = time.time()

            qid = occurrence['qid']['value'].split('/')[-1]
            if qid in current_node_qids:
                continue

            prop_nr = occurrence['p']['value'].split('/')[-1]
            wd_onto_qid = occurrence['onto_qid']['value'].split('/')[-1]
            wd_item_id = PBB_Core.WDItemID(value=wd_onto_qid, prop_nr=prop_nr)
            setattr(wd_item_id, 'remove', '')
            try:
                wd_item = PBB_Core.WDItemEngine(wd_item_id=qid, data=[wd_item_id])
                wd_item.write(login=login)

                PBB_Core.WDItemEngine.log(
                    'INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}'.format(ontology_id),
                            exception_type='',
                            message='successfully removed obsolete edges',
                            wd_id=qid,
                            duration=time.time() - start
                        ))
            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log(
                    'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}'.format(ontology_id),
                            exception_type=type(e),
                            message=e.__str__(),
                            wd_id=qid,
                            duration=time.time() - start
                        ))

        if obsolete_term:
            data = [
                PBB_Core.WDString(value=ontology_id, prop_nr=core_property_nr, rank='deprecated'),
            ]

            start = time.time()
            try:
                wd_item = PBB_Core.WDItemEngine(item_name='obo', domain='obo', data=data, use_sparql=True)
                if wd_item.create_new_item:
                    return
                qid = wd_item.write(login=login)

                PBB_Core.WDItemEngine.log(
                    'INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}'.format(ontology_id),
                            exception_type='',
                            message='successfully obsoleted the ',
                            wd_id=qid,
                            duration=time.time() - start
                        ))
            except Exception as e:
                print(e)
                PBB_Core.WDItemEngine.log(
                    'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                        .format(
                            main_data_id='{}'.format(ontology_id),
                            exception_type=type(e),
                            message=e.__str__(),
                            wd_id='',
                            duration=time.time() - start
                        ))


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    # biological process (GO:0008150), molecular function (GO:0003674), cellular component (GO:0005575) (Q5058355)
    root_objects = ['0008150', '0003674', '0005575']

    # continue_at = ''
    # stop_at = ''

    file_name = 'temp_GO_onto_map.json'
    if os.path.exists(file_name):
        f = open(file_name, 'r')
        local_qid_onto_map = json.loads(f.read())
        f.close()
    else:
        local_qid_onto_map = {}

    # Ontology ref item is the Wikidata 'Gene Ontolgy' item
    OBOImporter(root_objects=root_objects, ontology='GO', core_property_nr='P686',
                ontology_ref_item='Q135085', login=login, local_qid_onto_map=local_qid_onto_map)

if __name__ == '__main__':
    sys.exit(main())
