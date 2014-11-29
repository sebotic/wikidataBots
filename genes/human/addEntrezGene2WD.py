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
    
# Adding knowledge
#Chromosomes
chromosomes = dict()
chromosomes['1'] = "Q430258"
chromosomes['2'] = "Q638893"
chromosomes['3'] = "Q668633"
chromosomes['4'] = "Q836605"
chromosomes['5'] = "Q840741"
chromosomes['6'] = "Q540857"
chromosomes['7'] = "Q657319"
chromosomes['8'] = "Q572848"
chromosomes['9'] = "Q840604"
chromosomes['10'] = "Q840737"
chromosomes['11'] = "Q847096"
chromosomes['12'] = "Q847102"
chromosomes['13'] = "Q840734"
chromosomes['14'] = "Q138955"
chromosomes['15'] = "Q765245"
chromosomes['16'] = "Q742870"
chromosomes['17'] = "Q220677"
chromosomes['18'] = "Q780468"
chromosomes['19'] = "Q510786"
chromosomes['20'] = "Q666752"
chromosomes['21'] = "Q753218"
chromosomes['22'] = "Q753805"
chromosomes['22'] = "Q753805"
chromosomes['X'] = "Q61333"
chromosomes['Y'] = "Q202771"

#Entrez gene
f = open('entrezGenes.tsv', 'r')
entrezGeneLabel = dict() # Dictionary to capture Entrez identifiers and their label
for line in f:
    entrezGeneline = line.split('\t')
    entrezGeneLabel[entrezGeneline[0]] = entrezGeneline[1].strip() # entrezGeneline[0] = entrezGeneId, entrezGeneline[1] = primary label
    

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

put_throttle = 1
#references 
reference2entrezGene = pywikibot.ItemPage(repo, 'Q1345229')  
humanSpeciesPage = pywikibot.ItemPage(repo, u'Q5')
genePage = pywikibot.ItemPage(repo, u'Q7187')

# Initiate log files
successLog = open('/tmp/'+sys.argv[1]+'_succesfullyAdded.log', 'w')
multipleEntriesLog = open('/tmp/'+sys.argv[1]+'_multipleItems.log', 'w')
multipleMyGeneEntriesLog = open('/tmp/'+sys.argv[1]+'_multipleMyGeneEntries.log', 'w')
noLabelLog = open('/tmp/'+sys.argv[1]+'_noLabelsEntrezGene.log', 'w')
print "start"
with open(sys.argv[1], 'r') as myEntrezGenes:
    myEntrezGeneIds = myEntrezGenes.readlines()
for entrezGeneID in myEntrezGeneIds:
    entrezGeneID = entrezGeneID.strip()
    if entrezGeneLabel[entrezGeneID] == '-': # No label given ergo do nothing except logging the entrez gene identifier
        print "No Label"
        noLabelLog.write(entrezGeneID+'\n')    
    else: 
        itemcount = countItems(entrezGeneLabel[entrezGeneID])
        if itemcount >1 : # when multiple entries of a title exists do nothing except logging the entrez gene idetnfier
           multipleEntriesLog.write(entrezGeneID+'\n')
        else:
            if itemcount == 1 :
               data = getItems(entrezGeneLabel[entrezGeneID])    
               ID = data['search'][0]['id']
               print ID
            if itemcount == 0 : # create a new item page and populate from mygene.indo
               labels = []
               labels.append({"language":"en","value" : entrezGeneLabel[entrezGeneID]})
               data = {
                  "labels" : labels 
                  }
               New = repo.editEntity({},data,bot=False)
               ID = New['entity']['id']
               print ID
               
            item = pywikibot.ItemPage(repo, ID)
            print item.getID()
            successLog.write(entrezGeneID+": "+ID+"\n")
            addStatement(repo, item, 'P351', str(entrezGeneID), reference2entrezGene ) # P351 = Entrez gene
            # Add species
            addStatement(repo, item, 'P703', humanSpeciesPage, reference2entrezGene) #P703 = found in taxon
            # Add type "subclass of" P279 gene Q7187
            addStatement(repo, item, 'P279', genePage, reference2entrezGene) #P279 = subclass of
            # Get  details from MygeneInfo
            req=urllib2.Request("http://mygene.info/v2/gene/"+entrezGeneID, None, {'user-agent':'ProteinBoxBot'})
            print "http://mygene.info/v2/gene/"+entrezGeneID
            opener = urllib2.build_opener()
            f = opener.open(req)
            mygeneinfo = simplejson.load(f)
            if isinstance(mygeneinfo, list):
                multipleMyGeneEntriesLog.write(entrezGeneId+": "+"http://mygene.info/v2/gene/"+entrezGeneID+": Multiple Ensembl entries in mygene.info"+"\n")
                break
            # Add Ensembl Id's
            if "ensembl" in mygeneinfo: 
                ensemblEntries =  mygeneinfo["ensembl"]  # P594 = Entrez Gene Id
                if isinstance(ensemblEntries, list):
                   multipleMyGeneEntriesLog.write(entrezGeneID+": "+"http://mygene.info/v2/gene/"+entrezGeneID+": Multiple Ensembl entries in mygene.info"+"\n")
                else:
                   # Ensembl Gene
                   addIdentifier(repo, item, ensemblEntries["gene"], 'P594', reference2entrezGene) # P594 = Ensembl Gene Id
                   # Ensembl Transcript
                   addIdentifier(repo, item, ensemblEntries["transcript"], 'P704', reference2entrezGene) # P704 = Ensembl Transcript Id
    
            if "symbol" in mygeneinfo: addIdentifier(repo, item, mygeneinfo["symbol"], 'P353', reference2entrezGene) # P353 = gene symbol
            if "HGNC" in mygeneinfo: addIdentifier(repo, item, mygeneinfo["HGNC"], 'P354', reference2entrezGene) # P354 = HGNC ID
            if "homologene" in mygeneinfo: addIdentifier(repo, item, str(mygeneinfo["homologene"]["id"]), 'P593', reference2entrezGene) # P593 = homologene id
    
            if "refseq" in mygeneinfo: refseqEntries =  mygeneinfo["refseq"]
            if "rna" in refseqEntries: addIdentifier(repo, item, refseqEntries["rna"], 'P639', reference2entrezGene) # P639 = RefSeq RNA ID    
            #Add chromosome
            if "genomic_pos" in mygeneinfo: 
                if (isinstance(mygeneinfo["genomic_pos"], list)):
                   chromosome = mygeneinfo["genomic_pos"][0]["chr"]
                else: chromosome = mygeneinfo["genomic_pos"]["chr"]
                chromosomepage = pywikibot.ItemPage(repo, chromosomes[str(chromosome)])
                addStatement(repo, item, 'P1057', chromosomepage, reference2entrezGene)
        
print "Finished"