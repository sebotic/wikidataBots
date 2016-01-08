import PBB_Core
import PBB_login
import pprint
import requests
import sys

__author__ = 'Sebastian Burgstaller'
__license__ = 'AGPLv3'

"""
This script executes a SPARQL query and based on that looks for human genes which could match, it displays the whole
item and prompts whether the users wants to merge or do a different action. This allows to quickly find, clean and merge
many items
"""

prop_store = dict()


def lookup_symbol(symbol):
    query = '''
        SELECT ?gene WHERE {{
          ?gene wdt:P353 '{}' .

        }}
    '''.format(symbol)

    r = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

    for z in r:
        return z['gene']['value'].split('/')[-1]

    return None


def extract_sitelinks(sitelink_dict):
    base_url = 'https://{}.wikipedia.org/wiki/{}\n\t'
    sitelink_string = ''
    for wiki in sitelink_dict:
        lang = wiki[0:-4]
        title = sitelink_dict[wiki]['title']
        sitelink_string += base_url.format(lang, title)

    return sitelink_string

def print_item(qid):
    wd_item = PBB_Core.WDItemEngine(wd_item_id=qid, use_sparql=True)
    label = wd_item.get_label()
    description = wd_item.get_description()
    aliases = wd_item.get_aliases()
    sitelinks_string = extract_sitelinks(wd_item.get_wd_json_representation()['sitelinks'])

    statement_print = ''

    for stmt in wd_item.statements:
        # retrieve English prop label and store in prop_label dict to minimize traffic
        prop_nr = stmt.get_prop_nr()
        prop_label = ''
        if prop_nr not in prop_store:
            prop_item = PBB_Core.WDItemEngine(wd_item_id=prop_nr)
            prop_label = prop_item.get_label()
            prop_store[prop_nr] = prop_label
        else:
            prop_label = prop_store[prop_nr]

        item_label = stmt.get_value()
        item_id = ''
        if isinstance(stmt, PBB_Core.WDItemID):
            item_id = item_label
            # print(item_id)
            item = PBB_Core.WDItemEngine(wd_item_id='Q{}'.format(item_label))
            item_label = '{} (QID: Q{})'.format(item.get_label(), item_id)

        statement_print += 'Prop: {0:.<40} value: {1} \n    '.format('{} ({})'.format(prop_label, prop_nr), item_label)

    output = '''


    Item QID: {4}
    Item: {0} / {1} / {2}
    {3}
    {5}
    '''.format(label, description, aliases, statement_print, qid, sitelinks_string)

    print(output)


def main():

    print(sys.argv[1], sys.argv[2])
    # pwd = input('Password:')
    login_obj = PBB_login.WDLogin(user=sys.argv[1], pwd=sys.argv[1])

    prefix = '''
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>
    '''

    missing_go_query = '''
        SELECT distinct ?protein ?label WHERE {
          ?protein wdt:P279 wd:Q8054 .
          ?protein wdt:P703 wd:Q5 .
          OPTIONAL {
              ?protein rdfs:label ?label filter (lang(?label) = "en") .
              ?article schema:about ?protein .
          }
          FILTER NOT EXISTS {?protein wdt:P351 ?m} .
          FILTER NOT EXISTS {?protein wdt:P352 ?n} .
        }
        #GROUP BY ?protein
    '''

    results = PBB_Core.WDItemEngine.execute_sparql_query(prefix=prefix, query=missing_go_query)['results']['bindings']

    for count, x in enumerate(results):
        label = x['label']['value']
        protein_qid = x['protein']['value'].split('/')[-1]

        print_item(protein_qid)

        gene_qid = lookup_symbol(symbol=label)
        print('count:', count, 'Gene QID:', gene_qid)
        if gene_qid is not None:
            decision = input('Merge? (y):')

            if decision == 'y':
                data = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P279')]
                try:
                    wd_item = PBB_Core.WDItemEngine(wd_item_id=protein_qid, data=data)
                    wd_item.set_description(description='', lang='en')
                    wd_item.set_description(description='', lang='de')
                    wd_item.set_description(description='', lang='fr')
                    wd_item.set_description(description='', lang='nl')
                    wd_item.write(login=login_obj)

                    print('merge accepted')
                    merge_reply = PBB_Core.WDItemEngine.merge_items(from_id=protein_qid, to_id=gene_qid, login_obj=login_obj)
                    pprint.pprint(merge_reply)
                    # print('merge completed')
                except PBB_Core.MergeError as e:
                    pprint.pprint(e)
                    continue

                except Exception as e:
                    pprint.pprint(e)
                    continue

        else:
            pass

        if count > 20:
            break

if __name__ == '__main__':
    sys.exit(main())