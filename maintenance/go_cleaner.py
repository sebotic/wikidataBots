import PBB_Core
import PBB_login
import sys
import time
import pprint

__author__ = 'Sebastian Burgstaller'


class GOCleaner(object):
    def __init__(self, login):

        self.login_obj = login

        wdq_results = PBB_Core.WDItemList('CLAIM[686]', '686').wditems
        wd_go_terms = list(map(lambda z: z[2], wdq_results['props']['686']))
        go_qid_list = list(map(lambda z: 'Q{}'.format(z[0]), wdq_results['props']['686']))

        for count, go_term in enumerate(wd_go_terms):
            start = time.time()
            curr_qid = go_qid_list[wd_go_terms.index(go_term)]

            is_clean = True
            try:
                int(go_term)
            except ValueError as e:
                is_clean = False

            if not is_clean:
                new_go_term = go_term[-7:]
                data = [PBB_Core.WDString(value=new_go_term, prop_nr='P686')]
            else:
                continue

            try:
                go_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid, data=data)
                # pprint.pprint(gene_item.get_wd_json_representation())

                go_item.write(self.login_obj)

                PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=new_go_term,
                        exception_type='',
                        message='success',
                        wd_id=curr_qid,
                        duration=time.time() - start
                ))
                print(count, 'success', curr_qid, go_item.get_label(lang='en'))

            except Exception as e:
                print(count, 'error', curr_qid, go_term)
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    main_data_id=new_go_term,
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=curr_qid,
                    duration=time.time() - start
                ))


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    GOCleaner(login)


if __name__ == '__main__':
    sys.exit(main())
