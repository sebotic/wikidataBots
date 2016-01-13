__author__ = 'andra'

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ProteinBoxBot_Core")
import requests
import PBB_Core
import PBB_login
import PBB_settings
import pprint

import requests

login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
cookies = login.get_edit_cookie()
edit_token = login.get_edit_token()

count = 0
logfile = open('/tmp/WD_bot_run-2016-01-12_13:31.log', 'r')
for line in logfile.readlines():
    fields = line.split(",")
    if fields[0] != "ERROR":
        wdid = fields[5].strip()

        if wdid != "None":
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            }
            params = {
                        'action': 'wbgetentities',
                        'ids': wdid,
                        'format': 'json'
            }
            reply = requests.post(url="https://www.wikidata.org/w/api.php", data=params, headers=headers)
            wdoutput = reply.json()
            pprint.pprint(wdoutput)
            print(wdoutput['entities'][wdid]['lastrevid'])
            revid = wdoutput['entities'][wdid]['lastrevid']
            print(wdid, revid)
            count += 1

            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            }
            params = {
                        'action': 'edit',
                        'title': wdid,
                        'undo': revid,
                        'format': 'json',
                        'token': edit_token
            }
            reply = requests.post(url="https://www.wikidata.org/w/api.php", data=params, headers=headers, cookies=cookies)
            print(reply.text)
            
