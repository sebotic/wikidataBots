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

# Import the required libraries
import urllib2
import simplejson
import json
# -*- coding: utf-8  -*-
import pywikibot
import pprint
from pywikibot.data import api
import sys
import ProteinBoxBotFunctions
import ProteinBoxBotKnowledge
        
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()


# record a simple message
# client.captureMessage('ProteinBoxBot update on Human restarted')

pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(ProteinBoxBotFunctions.getItem(site, "Q18324078", "\\__"))
# try: 
with open(sys.argv[1], 'r') as myWikiDataItems:
#  try:
    wdItems = myWikiDataItems.readlines()
    for wdItem in wdItems:
        isuptodate = False
        wrongreference = False
        wdItem = wdItem.strip()
        itemFields = wdItem.split('\t')
        wikidataID = itemFields[1] # "Q18324078"
        wikidataEntry = ProteinBoxBotFunctions.getItem(site, wikidataID, "\\__")
        entrezID = itemFields[0] # "102636083"
        req=urllib2.Request("http://mygene.info/v2/gene/"+entrezID, None, {'user-agent':'ProteinBoxBot'})
        print "http://mygene.info/v2/gene/"+entrezID
        opener = urllib2.build_opener()
        f = opener.open(req)
        mygeneinfo = simplejson.load(f)
#        pp.pprint(wikidataEntry)

        mygeneinfoTimeStamp = "+0000000"+mygeneinfo['_timestamp']+"Z"
        claims = wikidataEntry['entities'][wikidataID]['claims']
        for claimProperty in claims.keys():
            for claim in claims[claimProperty]:
              if "references" in claim.keys():
                for reference in claim["references"]:
                    # pp.pprint(reference)
                    if 'P143' in reference["snaks"].keys():
                        for P143reference in reference["snaks"]["P143"]:
                            if P143reference["datavalue"]["value"]["numeric-id"] == 17939676: 
                                P143reference["datavalue"]["value"]["numeric-id"] = 1345229
                                wrongreference = True
                                print "Entrez reference fixed!!!!"
                    if not 'P143' in reference["snaks"].keys(): continue

                    if not 'P813' in reference["snaks"].keys(): reference["snaks"]['P813'] = []
                        #   if not isinstance(reference["snaks"]["P813"], list):  reference["snaks"]['P813'] = []
                    wdTimestamp = dict()
                    reference["snaks-order"]=['P143', 'P813']                 
                    wdTimestamp["datatype"]='time'
                    wdTimestamp["property"]='P813'
                    wdTimestamp["snaktype"]='value'
                    wdTimestamp["datavalue"]=dict()
                    wdTimestamp["datavalue"]["type"]='time'
                    wdTimestamp["datavalue"]["value"]=dict()
                    wdTimestamp["datavalue"]["value"]["after"]=0
                    wdTimestamp["datavalue"]["value"]["before"]=0
                    wdTimestamp["datavalue"]["value"]["calendarmodel"]='http://www.wikidata.org/entity/Q1985727'
                    wdTimestamp["datavalue"]["value"]["precision"]=11
                    for dataimport in reference["snaks"]['P813']:
                      if isinstance(dataimport["datavalue"]["value"]["time"], basestring): 
                        if dataimport["datavalue"]["value"]["time"] == mygeneinfoTimeStamp: 
                            isuptodate = True
                            continue
                    wdTimestamp["datavalue"]["value"]["time"]=mygeneinfoTimeStamp
                    wdTimestamp["datavalue"]["value"]["timezone"]=0
                    reference["snaks"]['P813']=[wdTimestamp]
                    # print mygeneinfoTimeStamp
                claim["qualifiers"]=dict()
                claim["qualifiers"]['P248'] = []
                qualifier = dict()
                claim["qualifiers"]['P248'].append(qualifier)
                qualifier['datatype']='wikibase-item'
                qualifier['property']='P248'
                qualifier['snaktype']='value'
                qualifier['datavalue']= dict()
                qualifier['datavalue']['type']='wikibase-entityid'
                qualifier['datavalue']['value']=dict()
                qualifier['datavalue']['value']['entity-type']='item'
                qualifier['datavalue']['value']['numeric-id']=17939676

        
        
        if not isuptodate or wrongreference:
            wikidataEntry.pop("success", None)
            wikidataEntry['entities'][wikidataID].pop("modified", None)
            wikidataEntry['entities'][wikidataID].pop("lastrevid", None)
            wikidataEntry['entities'][wikidataID].pop("ns", None)
            wikidataEntry['entities'][wikidataID].pop("pageid", None)
            wikidataEntry['entities'][wikidataID].pop("title", None)
            wikidataEntry['entities'][wikidataID].pop("type", None)

            token = repo.token(pywikibot.Page(repo, "Mecom adjacent non-protein coding RNA"), 'edit')

            request = api.Request(site=site,
                                action='wbeditentity',
                                format='json',
                                id=wikidataID,
                                bot=True,
                                token=token,
                                data=json.dumps(wikidataEntry['entities'][wikidataID]))
            # pp.pprint(localdata)
            data = request.submit()
            # pp.pprint(data)
            ID = data['entity']['id']
            print ID
          #  if "symbol" in mygeneinfo: 
          #       wikidataEntry = update

#  except:
#    client.captureException()
#    client.captureMessage('Last processed item: '+entrezID +" - "+wikidataID)

