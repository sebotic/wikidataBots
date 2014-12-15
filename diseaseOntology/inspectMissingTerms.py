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

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

pp = pprint.PrettyPrinter(indent=4)
namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

dourl = 'http://purl.obolibrary.org/obo/doid.owl'
request = urllib2.Request(dourl)
u = urllib2.urlopen(request)
do = u.read()

print "start"

# Load the owl file as an ETREE object
root = ET.fromstring(do)
doDate =  root.findall('.//oboInOwl:date', namespaces)
doversion = root.findall('.//owl:versionIRI', namespaces)
for name, value in doversion[0].items():
            doUrlversion = value

print "doUrl: "+doUrlversion
dateList = doDate[0].text.split(' ')[0].split(":")
print dateList[2]+"-"+dateList[1]+"-"+dateList[0]

# to capture the versioning of the owl, a wikidata entry for each release is needed. The                                                                            
# format is e.g. "Disease ontology release 2014-11-25
doVersion = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]
ProteinBoxBotFunctions.updateDiseaseOntologyVersion(site, repo, doVersion, dateList)

loadedDisOnt = ProteinBoxBotFunctions.getItemsByProperty("699")

inWikidata = loadedDisOnt['items']
# pp.pprint(inWikidata)
 
for diseaseClass in root.findall('.//owl:Class', namespaces):
    doid = diseaseClass.findall('.//oboInOwl:id', namespaces)[0].text
    if not doid in inWikidata:
        diseaseLabels = diseaseClass.findall('.//rdfs:label', namespaces)
        diseaseLabelsText = []
        diseaseSynonymsText = []
        diseaseWdIDs = []
        for diseaseLabel in diseaseLabels:
            token = repo.token(pywikibot.Page(repo, diseaseLabel.text.replace("<", "").replace(">", "")), 'edit')
            diseaseLabelsText.append(diseaseLabel.text.encode('ascii', 'replace'))
            wikidata = ProteinBoxBotFunctions.getItems(site, diseaseLabel.text.rstrip())
            # pp.pprint(wikidata)
            for result in wikidata["search"]:
                      if "label" in result.keys():
                        if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                          diseaseWdIDs.append(result["id"])
                        if wikidata["searchinfo"]["search"] == result["label"] :
                          diseaseWdIDs.append(result["id"])
                        if wikidata["searchinfo"]["search"] == result["label"].capitalize() :
                          diseaseWdIDs.append(result["id"])
        diseaseSynonyms = diseaseClass.findall('.//oboInOwl:hasExactSynonym', namespaces)
        for diseaseSynonym in diseaseSynonyms:
            diseaseSynonymsText.append(diseaseSynonym.text.encode('ascii', 'replace'))
            wikidata = ProteinBoxBotFunctions.getItems(site, diseaseSynonym.text.rstrip())
            for result in wikidata["search"]:
                if isinstance(result, dict):
                      if "label" in result.keys():
                        if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                          diseaseWdIDs.append(result["id"])
                        if wikidata["searchinfo"]["search"] == result["label"] :
                          diseaseWdIDs.append(result["id"])
                        if wikidata["searchinfo"]["search"] == result["label"].capitalize() :
                          diseaseWdIDs.append(result["id"])
        
        for wdItem in diseaseWdIDs:
          if not int(wdItem[1:]) in inWikidata:
            print ""
            sys.stdout.write(doid)
            sys.stdout.write('\t')
            sys.stdout.write(wdItem)
            sys.stdout.write('\t')
            claims = ProteinBoxBotFunctions.getWDProperties(site, wdItem)
            if 'P486' in claims:
                statements=[]
                for claim in claims['P486']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t MSH: "+",".join(statements))
            if 'P494' in claims:
                statements=[]
                for claim in claims['P494']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t ICD10: "+",".join(statements))
            if 'P493' in claims:
                statements=[]
                for claim in claims['P493']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t ICD9: "+",".join(statements))
            if 'P1550' in claims:
                statements=[]
                for claim in claims['P1550']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t ORPHANET: "+",".join(statements))
            if 'P1395' in claims:
                statements=[]
                for claim in claims['P1395']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t NCI: "+",".join(statements))
            if 'P492' in claims:
                statements=[]
                for claim in claims['P492']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t OMIM: "+",".join(statements))
            if 'P557' in claims:
                statements=[]
                for claim in claims['P557']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t DiseasesDB: "+",".join(statements))
            if 'P563' in claims:
                statements=[]
                for claim in claims['P563']:
                    statements.append(claim['mainsnak']['datavalue']['value'])
                sys.stdout.write("\t DiseasesDB: "+",".join(statements))
                
sys.exit()  
