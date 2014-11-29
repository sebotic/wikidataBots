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
   finalResult = 0
   for item in data['search']:
       if (itemtitle == item['label']):
           finalResult = finalResult + 1
   return finalResult
   
def itemExists(itemtitle):
    itemFound = False
    if countItems(itemtitle) > 0:
        itemFound = True
    return itemFound 
      
def getWDProperties(wdItem):
    params = {'action':'wbgetclaims', 'entity':wdItem}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def getWDProperty(wdItem, wdProperty):
    params = {'action':'wbgetclaims', 'entity':wdItem, 'property':wdProperty}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def countWDProperties(wdItem):
    return len(getWDProperties(wdItem))  
    
def hasProperty(wdItem, wdProperty):
    if len(getWDProperty(wdItem, wdProperty)[wdProperty]) == 1:
        return True
    else: 
        return False     
        
def setAlias(repo, item, itemLabel, alias):
    token = repo.token(pywikibot.Page(repo, itemLabel), 'edit')
    params = {'action':'wbsetaliases', 'language':'en', 'id':item, 'set':alias, 'bot':True, 'token':token}
    request = api.Request(site=site,**params)
    data = request.submit()
    print data
        
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
if len(sys.argv) != 2:
    print "Usage: python ProteinBoxBoxTemplate.py <fileNameWithIds>"
    print " "
    print "For details see <>" #FIXME point to details documentation page when finished
else:
  # Initiate log files
  successLog = open(sys.argv[1]+'_succesfullyAdded.log', 'w')
  multipleEntriesLog = open(sys.argv[1]+'_multipleItems.log', 'w')
  multipleMyGeneEntriesLog = open(sys.argv[1]+'_multipleMyGeneEntries.log', 'w')
  noLabelLog = open(sys.argv[1]+'_noLabelsEntrezGene.log', 'w')
  typeErrorLog = open(sys.argv[1]+'_typeErrorsEntrezGene.log', 'w')
  multiplesubClassLog = open('/tmp/'+sys.argv[1]+'_multipleSubclasses.log', 'w')

  # A file with both an identifier and a label is required
  # The file should contain (separated by '\t')
  # 1. Globally unique identifier (required) Entry gene id
  # 2. Symbol
  # 3. Synonym
  # 4. Label 
  
  
  with open(sys.argv[1], 'r') as myWikiDataItems:
    reference2resource = pywikibot.ItemPage(repo, 'Q17939676') # NCBI Homo sapiens Annotation Release 106
    resourceWDId= pywikibot.ItemPage(repo, 'Q7187') # gene
    wdItems = myWikiDataItems.readlines()
    for wdItem in wdItems:
      try:  
          wdItem = wdItem.strip()
          itemFields = wdItem.split('\t')
          print len(itemFields)
          itemID = itemFields[0]
          itemmainAlias = itemFields[1]
          itemotherAlias = itemFields[2]
          itemLabel = itemFields[3]
          if itemLabel == "-": 
              continue
          #print itemID
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
                   if hasProperty(ID, 'P279'):
                       if not getWDProperty(ID, 'P279')['P279'][0]['mainsnak']['datavalue']['value']['numeric-id'] == 7187:
                           multiplesubClassLog.write(itemID+'\t'+getWDProperty(ID, 'P279')['P279'][0]['mainsnak']['datavalue']['value']['numeric-id']+'\n')
                           continue
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
                successLog.flush()
                addStatement(repo, item, 'P351', str(itemID), reference2resource) # Entrez Gene ID 
                addStatement(repo, item, 'P279', genePage, reference2resource) # subclass of Gene
                addStatement(repo, item, 'P703', humanSpeciesPage,  reference2resource) # found in taxon human 
                setAlias(repo, ID, itemLabel, itemmainAlias)
                if not (itemotherAlias == "-"): setAlias(repo, ID, itemLabel, itemotherAlias)
      except TypeError as e:
            typeErrorLog.write(itemID)      
  print "Finished"