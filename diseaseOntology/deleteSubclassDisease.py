#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author:Andra Waagmeester (andra@waagmeester.net)

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

# import the necessary libraries
import urllib2
import simplejson
import json
import xml.etree.ElementTree as ET
from datetime import date, timedelta
import pprint
import sys
import pywikibot
from pywikibot.data import api
# ProteinBoxBotFunctions is a python library that contains function to interact with the Wikidata API
import ProteinBoxBotFunctions 
# ProteinBoxBotKnowledge contains mapping to resources in the form of wikidata identifiers. In the future we might want to 
# store these in config files. 
import ProteinBoxBotKnowledge 

def todelete(site, localdata, wdid):
    result = False
    i = 0
    if 'P279' in localdata['entities'][wdid]['claims'].keys():
     for subclass in localdata['entities'][wdid]['claims']['P279']:
      if subclass['mainsnak']['datavalue']['value']['numeric-id'] == 12136:
       if 'references' in subclass.keys():    
        for reference in subclass['references']:
            if 'P143' in reference['snaks'].keys():
                for importedFrom in reference['snaks']['P143']:
                    if importedFrom['datavalue']['value']['numeric-id'] == 5282129:
                        result = True
                        break
            # if not 'P813' in reference['snaks'].keys(): result = False
      if result:
            print localdata['entities'][wdid]['claims']['P279'][i]['id']
            request = api.Request(site=site,
                                     action='wbremoveclaims',
                                     claim=localdata['entities'][wdid]['claims']['P279'][i]['id'],
                                     token=token,
                                     bot=True)
            data = request.submit()
      i=i+1

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

pp = pprint.PrettyPrinter(indent=4)

req = urllib2.Request("http://wdq.wmflabs.org/api?q=claim%5B699%5D&props=699", None, {'user-agent':'proteinBoxBot'})
opener = urllib2.build_opener()
f = opener.open(req)
loadedDisOnt = simplejson.load(f)
pp.pprint(loadedDisOnt['items'])

inWikidata = loadedDisOnt['items']
counter = 1
for wdid in inWikidata:
    token = repo.token(pywikibot.Page(repo, str(wdid)), 'edit')
    localdata=ProteinBoxBotFunctions.getItem(site, "Q"+str(wdid) , token)
    
    todelete(site, localdata, "Q"+str(wdid))

    print counter
    counter= counter+1
