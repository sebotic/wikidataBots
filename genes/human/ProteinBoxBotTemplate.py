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

# Define the funcitons.

def getClaims(wdItem, claimProperty):
    params = {
    			'action' :'wbgetclaims' ,
                'entity' : wdItem.getID(),
    			'property': claimProperty,
             }
    request = api.Request(site=site,**params)
    return request.submit()
   
def countClaims(wdItem, claimProperty):
    data = getClaims(wdItem, claimProperty)
    return len(data["claims"][claimProperty])

def claimExists(wdItem, claimProperty, claimValue):
    data = getClaims(wdItem, claimProperty)
    pp = pprint.PrettyPrinter(indent=4)
    if len(data["claims"]) > 0:
      for claim in data["claims"][claimProperty]:
        if isinstance(claimValue, basestring):
          if str(claim['mainsnak']['datavalue']['value']) == str(claimValue):
            return True
        if isinstance(claimValue, pywikibot.page.ItemPage):
          if str(claim['mainsnak']['datavalue']['value']['numeric-id']) == str(claimValue.getID())[1:]:
            return True
      return False # end for loop
    else: return False # len(data["claims"]) == 0

'''
addStatement:
 A function to add individual claims to a WikiData Entry: e.g. 
Arguments:
   defrepo: the repository under scrutiny e.g. repo = site.data_repository()
   defitem: The item to which the statement applies. 
   propertyKey: the property key is the value under which the property is known in WikiData (e.g. P594 = Entrez Gene Id)
   propertyValue: the property value. This is either a literal or a WikiData page
   importedfrom: the authoritive source from which the statement was derived
'''
def addStatement(defrepo, defitem, propertyKey, propertyValue, importedfrom):
    print propertyValue
    if not claimExists(defitem, propertyKey, propertyValue):
        claim = pywikibot.Claim(defrepo, propertyKey)
        claim.setTarget(propertyValue)
        statedin = pywikibot.Claim(defrepo, 'p143') # Imported from
        statedin.setTarget(importedfrom)
        defitem.addClaim(claim)
        claim.addSource(statedin, bot=True)

'''
addIdentifier: 
  A function to add an external identifier to a data repository
  Arguments
     subrepo: the repository under scrutiny e.g. repo = site.data_repository()
     subitem: The item to which the statement applies. 
     identifierVar: The identifier to be added
     wikidataProperty: the property value. This is either a literal or a WikiData page
     reference: the authoritive source from which the statement was derived
'''
def addIdentifier(subrepo, subitem, identifierVar, wikidataProperty, reference):
    print wikidataProperty
    if isinstance(identifierVar, basestring):
        if not claimExists(subitem, wikidataProperty, identifierVar):
           addStatement(subrepo, subitem, wikidataProperty, identifierVar, reference)    
    else:
        for identifier in identifierVar:
           if not claimExists(subitem, wikidataProperty, identifier)    :
              addStatement(subrepo, subitem, wikidataProperty, identifier, reference)
       
def getItems(itemtitle):
  params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
  request = api.Request(site=site,**params)
  return request.submit()
	
def countItems(itemtitle):
   data = getItems(itemtitle)
   return len(data['search'])
   
def itemExists(itemtitle):
    itemFound = False
    if countItems(itemtitle) > 0:
        itemFound = True
    return itemFound 
      
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

#references 
## databases
reference2entrezGene = pywikibot.ItemPage(repo, u'Q1345229')  
reference2ensembl = pywikibot.ItemPage(repo, u'Q1344256')

## species 
humanSpeciesPage = pywikibot.ItemPage(repo, u'Q5')
mouseSpeciesPage = pywikibot.ItemPage(repo, u'')
genePage = pywikibot.ItemPage(repo, u'Q7187')
print len(sys.argv)
if len(sys.argv) != 4:
    print "Usage: python ProteinBoxBoxTemplate.py <fileNameWithIds> <WikiDataResourceID> <WikiDataInstanceID>"
    print " "
    print "For details see <>" #FIXME point to details documentation page when finished
else:
  # Initiate log files
  successLog = open('/tmp/'+sys.argv[1]+'_succesfullyAdded.log', 'w')
  multipleEntriesLog = open('/tmp/'+sys.argv[1]+'_multipleItems.log', 'w')
  multipleMyGeneEntriesLog = open('/tmp/'+sys.argv[1]+'_multipleMyGeneEntries.log', 'w')
  noLabelLog = open('/tmp/'+sys.argv[1]+'_noLabelsEntrezGene.log', 'w')
  typeErrorLog = open('/tmp/'+sys.argv[1]+'_typeErrorsEntrezGene.log', 'w')

  # A file with both an identifier and a label is required
  # The file should contain (separated by '\t')
  # 1. Globally unique identifier (required)
  # 2. Wikidata property of the Global identifier (required)
  # 2. A label (required)
  # 3. A description (optional)
  
  with open(sys.argv[1], 'r') as myWikiDataItems:
    reference2resource = pywikibot.ItemPage(repo, sys.argv[2]) 
    resourceWDId= pywikibot.ItemPage(repo, sys.argv[3]) 
    wdItems = myWikiDataItems.readlines()
    for wdItem in wdItems:
      try:  
          wdItem = wdItem.strip()
          itemFields = wdItem.split('\t')
          itemID = itemFields[0]
          itemIDprop = itemFields[1]
          itemLabel = itemFields[2]
          if len(itemFields) == 3:
              itemDescription = itemFields[2]
          print itemID
          # First count the number of occurences in WikiData for the given label
          itemcount = countItems(itemLabel)
          print itemcount
          if itemcount >1 : # when multiple entries of a title exists do nothing except logging the entrez gene idetnfier
               multipleEntriesLog.write(itemID+'\n')
          else:
                if itemcount == 1 :
                   data = getItems(itemLabel)    
                   ID = data['search'][0]['id']
                   print ID
                if itemcount == 0 : # create a new item page and populate from mygene.indo
                   labels = []
                   labels.append({"language":"en","value" : itemLabel})
                   data = {
                      "labels" : labels 
                      }
                   New = repo.editEntity({},data,bot=True)
                   ID = New['entity']['id']
                   print ID
               
                item = pywikibot.ItemPage(repo, ID)
                print item.getID()
                successLog.write(itemID+": "+ID+"\n")
                addStatement(repo, item, itemIDprop, str(itemID), reference2resource) 
                addStatement(repo, item, 'P31', resourceWDId,  reference2resource) # It is an instance of 
      except TypeError as e:
            typeErrorLog.write(itemID)      
  print "Finished"