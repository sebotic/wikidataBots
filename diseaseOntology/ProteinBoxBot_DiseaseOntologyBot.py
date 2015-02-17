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

import urllib2
import simplejson
import json
import xml.etree.ElementTree as ET
from datetime import date, timedelta
import pprint
import sys
import traceback
import pywikibot
from pywikibot.data import api
import ProteinBoxBotFunctions
import ProteinBoxBotKnowledge
from raven import Client
    
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

# Login to getSentry service
client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
# client.captureMessage('ProteinBoxBot started adding diseases')
try:
    # Get all WikiData entries that contain a WikiData ID
    print "Getting all terms with a disease ontology in WikiData"
    inWikidata = ProteinBoxBotFunctions.getItemsByProperty("699")['items']
    tempList = []
    for i in inWikidata:
        tempList.append("DOID:"+str(i))
    inWikidata = tempList
    


    # Get the latest Disease Ontology version and its timestamp
    print "Getting the Disease Ontology"
    diseaseOntology = ProteinBoxBotFunctions.getLatestDiseaseOntology()
    # Get the timestamp from Disease ontology
    diseaseOntologyTimeStamp = ProteinBoxBotFunctions.getDiseaseOntologyTimeStamp(diseaseOntology)

    # Update the WikiData entry for this version of Disease ontology 
    print "Update the latest version of Disease Ontology on Wikidata"
    ProteinBoxBotFunctions.updateDiseaseOntologyVersion(site, repo, diseaseOntology)

    # Take a term from DO and process it
    namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

    index =0
    # sys.exit()
    print inWikidata
    for diseaseClass in diseaseOntology.findall('.//owl:Class', namespaces):
        obsolete = False
        # Is it obsolete?
        if len(diseaseClass.findall('.//owl:deprecated', namespaces))>0:
            # if so add the deprecated flag
            obsolete = True
    
        # get all the data that needs to be added to wikidata
        # Get the Disease Ontology Identifier
        doid = diseaseClass.findall('.//oboInOwl:id', namespaces)[0].text
        print doid
        print type(doid)
        print doid in inWikidata 
        
        # if doid in inWikidata:
        #    print "Niet nu"
          # ProteinBoxBotFunctions.updateDOWDItem(site, repo, diseaseClass, diseaseOntologyTimeStamp, obsolete, diseaseOntology)
        # else:   
        ProteinBoxBotFunctions.addOrUpdateDOWDItem(site, repo, diseaseClass, diseaseOntologyTimeStamp, obsolete, diseaseOntology)
        '''
        index = index + 1
        if index == 1000:
           sys.exit()
        '''
except Exception, err:
     print traceback.format_exc()
     #client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
     client.captureException()
