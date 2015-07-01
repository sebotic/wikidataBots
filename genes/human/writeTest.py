#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Authors: 
  Andra Waagmeester (andra' at ' micelio.be)

This file is part of ProteinBoxBot.

ProteinBoxBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ProteinBoxBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProteinBoxBot.  If not, see <http://www.gnu.org/licenses/>.
'''

__author__ = 'Andra Waagmeester'
__license__ = 'GPL'

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
import urllib
import urllib3
import certifi
import requests

import sys
import mygene_info_settings
try:
    import simplejson as json
except ImportError as e:
    import json

query = 'https://test.wikidata.org/w/api.php?action=wbgetentities{}{}{}{}'.format(
    '&sites=enwiki',
    '&languages=en',
    '&ids={}'.format("Q1232"),
    '&format=json'
)
print "test"
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
request = http.request("GET", query)
wikidata = json.loads(request.data)
PBB_Debug.prettyPrint(wikidata)


wikidata['entities']["Q1232"].pop("modified", None)
wikidata['entities']["Q1232"].pop("lastrevid", None)
wikidata['entities']["Q1232"].pop("ns", None)
wikidata['entities']["Q1232"].pop("pageid", None)
wikidata['entities']["Q1232"].pop("title", None)
wikidata['entities']["Q1232"].pop("type", None)

claims =wikidata["entities"]["Q1232"]["claims"]
sys.exit()
newclaim = dict()
newclaim["rank"] = "normal"
newclaim["type"] = "statement"
mainsnak = dict()
mainsnak["datatype"]= 'url'
mainsnak["property"]='P31'
mainsnak["snaktype"]='value'
datavalue=dict()
datavalue['type']='string'
datavalue['value']='http://www.ekeren.be'
mainsnak['datavalue']=datavalue
newclaim["mainsnak"] = mainsnak
claims.append(newclaim)

PBB_Debug.prettyPrint(wikidata)

print "test"
login_obj = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
cookies = login_obj.get_edit_cookie()
edit_token = login_obj.get_edit_token()

query = 'https://test.wikidata.org/w/api.php'
token = edit_token
headers = {'content-type': 'application/x-www-form-urlencoded'}

fields = {
    'action': "wbeditentity",
    "data": json.dumps(wikidata["entities"]["Q1232"]),
    'token': token,
    'id': "Q1232",
    'format': "json",
    'bot': True,
}


reply = requests.post(query, headers=headers, data=fields, cookies=cookies)
json_data = json.loads(reply.text)
PBB_Debug.prettyPrint(json_data)

