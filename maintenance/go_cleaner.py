import PBB_Core
import PBB_login
import sys
import time
import argparse

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__licence__ = 'AGPLv3'

"""
This script retrieves all Wikidata items with identifiers which lack a certain prefix and adds the prefix for all items.
It will only work if the GO term ID is the last digits of a string.
"""


class GOCleaner(object):
    def __init__(self, login, prop_nr, prefix_str, separator=':'):
        """
        A class to take care of fixing certain identifer prefixes
        :param login: The Wikidata login object instance of PBB_login.WDLogin()
        :param prop_nr: the property number of the identifier the prefix should be fixed for
        :param prefix_str: the prefix string. e.g. 'GO', 'DOID'
        :param separator: the separator character between prefix and string
        """

        self.login_obj = login

        query = '''
            SELECT distinct ?s ?id WHERE {{
                ?s wdt:{0} ?id .
                FILTER(!REGEX(?id, "^{1}{2}[0-9]", "i"))
            }}
        '''.format(prop_nr, prefix_str, separator)

        qids_to_clean = set()
        for x in PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']:
            qids_to_clean.add(x['s']['value'].split('/')[-1])

        print('Cleaning up', len(qids_to_clean), 'items.')

        for count, curr_qid in enumerate(qids_to_clean):
            start = time.time()
            clean_gos = []
            print(curr_qid)

            cleanup_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid)
            for wd_value in cleanup_item.statements:
                if wd_value.get_prop_nr() == prop_nr:
                    go_value = wd_value.get_value()

                    if not go_value.startswith(prefix_str):
                        clean_gos.append(PBB_Core.WDString(value=prefix_str + separator + go_value, prop_nr=prop_nr))

            try:
                go_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid, data=clean_gos)
                go_item.write(self.login_obj)

                PBB_Core.WDItemEngine.log('INFO', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='',
                        message='success',
                        wd_id=curr_qid,
                        duration=time.time() - start
                ))
                print(count, 'success', curr_qid, go_item.get_label(lang='en'))

            except Exception as e:
                print(count, 'error', curr_qid)
                PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=curr_qid,
                    duration=time.time() - start
                ))


def main():
    parser = argparse.ArgumentParser(description='Gene Ontology prefix cleaner')
    parser.add_argument('--user', action='store', help='Username on Wikidata', required=True)
    parser.add_argument('--pwd', action='store', help='Password on Wikidata', required=True)
    parser.add_argument('--prefix', action='store', help='The prefix which should be added', required=True)
    parser.add_argument('--prop-nr', action='store', help='The Wikidata property number where the '
                                                          'prefixes need to be checked and fixed', required=True)
    parser.add_argument('--separator', action='store', help='The separator character between prefix '
                                                            'and actual identifier. ":" as default.',
                        required=False, default=':')

    args = parser.parse_args()
    print(args.user, args.pwd, args.prefix, args.prop_nr, args.separator)
    login = PBB_login.WDLogin(user=args.user, pwd=args.pwd)

    GOCleaner(login, prop_nr=args.prop_nr, prefix_str=args.prefix, separator=args.separator)


if __name__ == '__main__':
    sys.exit(main())
