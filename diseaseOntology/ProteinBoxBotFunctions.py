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
import time
import datetime

# Define the funcitons.

def getClaims(site, wdItem, claimProperty):
    params = {
    			'action' :'wbgetclaims' ,
                'entity' : wdItem.getID(),
    			'property': claimProperty,
             }
    request = api.Request(site=site,**params)
    return request.submit()
   
def countClaims(site, wdItem, claimProperty):
    data = getClaims(site, wdItem, claimProperty)
    return len(data["claims"][claimProperty])

def claimExists(site, wdItem, claimProperty, claimValue):
    data = getClaims(site, wdItem, claimProperty)
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
def addStatement(site, defrepo, defitem, propertyKey, propertyValue, importedfrom):
    if not claimExists(site, defitem, propertyKey, propertyValue):
        print propertyValue
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
def addIdentifier(site, subrepo, subitem, identifierVar, wikidataProperty, reference):
    if isinstance(identifierVar, basestring):
        if not claimExists(site, subitem, wikidataProperty, identifierVar):
           addStatement(site, subrepo, subitem, wikidataProperty, identifierVar, reference)    
    else:
        for identifier in identifierVar:
           if not claimExists(site, subitem, wikidataProperty, identifier)    :
              addStatement(site, subrepo, subitem, wikidataProperty, identifier, reference)
       
def getItems(site, itemtitle):
  params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
  request = api.Request(site=site,**params)
  return request.submit()
	
def countItems(site, itemtitle):
   data = getItems(site, itemtitle)
   finalResult = 0
   for item in data['search']:
       if (itemtitle == item['label']):
           finalResult = finalResult + 1
   return finalResult
   
def itemExists(site, itemtitle):
    itemFound = False
    if countItems(site, itemtitle) > 0:
        itemFound = True
    return itemFound 
      
def getWDProperties(site, wdItem):
    params = {'action':'wbgetclaims', 'entity':wdItem}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def getWDProperty(site, wdItem, wdProperty):
    params = {'action':'wbgetclaims', 'entity':wdItem, 'property':wdProperty}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def countWDProperties(site, wdItem):
    return len(getWDProperties(site, wdItem))  
    
def hasProperty(site, wdItem, wdProperty):
    if len(getWDProperty(site, wdItem, wdProperty)[wdProperty]) == 1:
        return True
    else: 
        return False     
        
def setAlias(site, repo, item, itemLabel, alias):
    token = repo.token(pywikibot.Page(repo, itemLabel), 'edit')
    params = {'action':'wbsetaliases', 'language':'en', 'id':item, 'set':alias, 'bot':True, 'token':token}
    request = api.Request(site=site,**params)
    data = request.submit()
    print data 
  
  
def isGene(site, repo, wdItem):
    if (pywikibot.ItemPage(repo, wdItem)==ProteinBoxBotKnowledge.mouseSpeciesPage):
        return True
    else:
        return False

def isHuman(site, repo, wdItem):
    if (pywikibot.ItemPage(repo, wdItem)==ProteinBoxBotKnowledge.humanSpeciesPage):
        return True
    else: 
        return False


def createNewPage(site, token):
    params = {'action':'wbeditentity','format' : 'json', 'new':'item', 'data':'{}', 'bot':True, 'token':token}
    request = api.Request(site=site,**params)
    return request.submit()
    
def addLabel(localdata, label):
    englishLabel = dict()
    englishLabel['language']='en'
    englishLabel['value']=label
    englishLabels=dict()
    englishLabels['en']=englishLabel
    localdata['entity']['labels']=englishLabels
    return localdata

def addLabel2(localdata, label, wdid):
    englishLabel = dict()
    englishLabel['language']='en'
    englishLabel['value']=label
    englishLabels=dict()
    englishLabels['en']=englishLabel
    localdata['entities'][wdid]['labels']=englishLabels
    return localdata

def addAliases(localdata, alias, otheraliases):
    aliases={'en':[]}
    if (otheraliases != "-"):
       otherAliases=otheraliases
       aliasesList = otherAliases
       for tempAlias in aliasesList:
         alias=dict()
         alias['language']='en'
         alias['value']=tempAlias
         aliases['en'].append(alias)
    localdata['entity']['aliases']=aliases
    return localdata
    
def addAliases2(localdata, alias, otheraliases, wdid):
    aliases={'en':[]}
    if (otheraliases != "-"):
       otherAliases=otheraliases
       aliasesList = otherAliases
       for tempAlias in aliasesList:
         alias=dict()
         alias['language']='en'
         alias['value']=tempAlias
         aliases['en'].append(alias)
    localdata['entities'][wdid]['aliases']=aliases
    return localdata

def addClaims(localdata, property, values, datatype):
    localdata["entity"]["claims"][property] = []
    localvalues = []
    if isinstance(values, list): 
        localvalues = values
    else:
        localvalues.append(values)
        
    for value in localvalues:
        statement = dict()
        statement["rank"]="normal"
        statement["type"]="statement"
        mainsnak =dict()
        statement["mainsnak"]=mainsnak      
        # mainsnak["datatype"]=datatype 
        mainsnak['property']=property    
        mainsnak['datavalue']=dict()
        if datatype=='string':
            mainsnak['datavalue']['type']='string'
            mainsnak['datavalue']['value']=value
            mainsnak['snaktype']='value'
        elif datatype=='wikibase-entityid':
            mainsnak['datavalue']['type']='wikibase-entityid'
            mainsnak['datavalue']['value']=dict()
            mainsnak['datavalue']['value']['entity-type']='item'
            mainsnak['datavalue']['value']['numeric-id']=value
            mainsnak['snaktype']='value'
        mainsnak["type"]="statement"
        mainsnak["rank"]="normal"
        statement["references"]=[]
        statement["references"]=addReference(statement["references"], 'P143', 5282129)      
        statement = setQualifier2Claim(statement) #TODO change statement to claim
        localdata["entity"]["claims"][property].append(statement)
    return localdata
    
# This needs to be reviewed and reimplemented

def addClaims2(localdata, property, values, datatype, wdid): 
    localdata["entities"][wdid]["claims"][property] = []
    localvalues = []
    if isinstance(values, list): 
        localvalues = values
    else:
        localvalues.append(values)
        
    for value in localvalues:
        statement = dict()
        statement["rank"]="normal"
        statement["type"]="statement"
        mainsnak =dict()
        statement["mainsnak"]=mainsnak      
        # mainsnak["datatype"]=datatype 
        mainsnak['property']=property    
        mainsnak['datavalue']=dict()
        if datatype=='string':
            mainsnak['datavalue']['type']='string'
            mainsnak['datavalue']['value']=value
            mainsnak['snaktype']='value'
        elif datatype=='wikibase-entityid':
            mainsnak['datavalue']['type']='wikibase-entityid'
            mainsnak['datavalue']['value']=dict()
            mainsnak['datavalue']['value']['entity-type']='item'
            mainsnak['datavalue']['value']['numeric-id']=value
            mainsnak['snaktype']='value'
        mainsnak["type"]="statement"
        mainsnak["rank"]="normal"
        statement["references"]=[]
        statement["references"]=addReference(statement["references"], 'P143', 5282129)
        statement = setQualifier2Claim(statement) #TODO change statement to claim
        localdata["entities"][wdid]["claims"][property].append(statement)
    return localdata

def addReference(references, property, itemId):
    reference = dict()
    snaks = dict()
    reference["snaks"] = snaks
    snaks[property]=[]
    reference['snaks-order']=['P143']
    snak=dict()
    snaks[property].append(snak)
    snak['property']=property
    snak["snaktype"]='value'
    snak["datatype"]='wikibase-item'
    snak["datavalue"]=dict()
    snak["datavalue"]["type"]='wikibase-entityid'
    snak["datavalue"]["value"]=dict()
    snak["datavalue"]["value"]["entity-type"]='item'
    snak["datavalue"]["value"]["numeric-id"]=itemId
    reference = setDateRetrievedTimestamp(reference)
    references.append(reference)
    return references    

def setDateRetrievedTimestamp(reference):
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('+0000000%Y-%m-%dT00:00:00Z')

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
    wdTimestamp["datavalue"]["value"]["time"]=timestamp
    wdTimestamp["datavalue"]["value"]["timezone"]=0
    reference["snaks"]['P813']=[wdTimestamp]
    return reference

def setQualifier2Claim(claim):
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
    qualifier['datavalue']['value']['numeric-id']=18553024
    return claim


def getItem(site, wdItem, token):
    request = api.Request(site=site,
                          action='wbgetentities',
                          format='json',
                          ids=wdItem)
    
    return request.submit()
