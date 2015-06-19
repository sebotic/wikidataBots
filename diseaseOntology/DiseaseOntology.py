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
sys.path.append("/Users/andra/wikidatabots/ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import urllib2
import xml.etree.cElementTree as ET
import sys
import DiseaseOntology_settings

class diseaseOntology():
    def __init__(self):      
        self.content = ET.fromstring(self.download_disease_ontology())
        self.version_date = self.getWDDiseaseOntologyTimeStamp()
        self.version_iri = self.getDiseaseOntologyVersionIRI()
        # self.wd_search_term = self.getWDSearchTerm()
        # updateDiseaseOntologyVersionInWD()
        
        # Get all WikiData entries that contain a WikiData ID
        print "Getting all terms with a Disease Ontology ID in WikiData"
        doWikiData_id = dict()
        DoInWikiData = PBB_Core.WDItemList("CLAIM[699]", "699")
        # PBB_Debug.prettyPrint(DoInWikiData.wditems)
        for diseaseItem in DoInWikiData.wditems["props"]["699"]:
           print diseaseItem[2]
           doWikiData_id["DOID:"+str(diseaseItem[2])]=diseaseItem[0] # TODO: rm DOID: once prefix issue in wikidta is fixed
 
        for doClass in self.content.findall('.//owl:Class', DiseaseOntology_settings.getDoNameSpaces()):
            diseaseClass = disease(doClass)
            if diseaseClass.do_id in doWikiData_id.keys():
                diseaseClass.wikidata_id = "Q"+str(diseaseItem[0])
            else:
                diseaseClass.wikidata_id = None
            print diseaseClass.do_id
            print diseaseClass.wikidata_id
            print diseaseClass.label
            print diseaseClass.synonyms
            print diseaseClass.xrefs
        
        
    
    def download_disease_ontology(self):
        """
        Downloads the latest version of disease ontology from the URL specified in DiseaseOntology_settings
        """
        request = urllib2.Request(DiseaseOntology_settings.getdoUrl())
        u = urllib2.urlopen(request)
        do = u.read()
        return do
     
    def getDiseaseOntologyTimeStamp(self):
        """
        Extract the version date from Disease Ontology
        """
        doDate =  self.content.findall('.//oboInOwl:date', DiseaseOntology_settings.getDoNameSpaces())
        return doDate
        
    def getWDDiseaseOntologyTimeStamp(self):
        """
        Converts a Disease Ontology version date to the format recognized by WikiData
        """
        doDate = self.getDiseaseOntologyTimeStamp()
        dateList = doDate[0].text.split(' ')[0].split(":")
        timeList = doDate[0].text.split(' ')[1].split(":")
        return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+"00:00:00Z"  
    
    def getDiseaseOntologyVersionIRI(self):
        """
        Extracts the URL from where the disease ontology version applicable
        """
        doVersion = self.content.findall('.//owl:versionIRI', DiseaseOntology_settings.getDoNameSpaces())
        #for name, value in doversion[0].items():
        #    doUrlversion = value
        #return doUrlversion
        
           
    # def updateDiseaseOntologyVersionInWD(self):
    #    pass
        
class  disease(object):
    def __init__(self, object):
        """
        constructor
        :param wd_do_content: Wikidata item id
        :param do_id: Identifier of the disease in Disease Ontology
        :param label: Primary label of the disease in Disease Ontology
        :param synonyms: All synonyms for the disease captured in the Disease Ontology
        :param xrefs: a dictionary with all external references of the Disease captured in the Disease Ontology
        """
        self.wd_do_content = object
        self.do_id = self.getDoValue(self.wd_do_content, './/oboInOwl:id')[0].text
        self.label = self.getDoValue(self.wd_do_content, './/rdfs:label')[0].text
        self.synonyms = []
        for synonym in self.getDoValue(self.wd_do_content, './/oboInOwl:hasExactSynonym'):
            self.synonyms.append(synonym.text)
        self.xrefs = dict()
        for xref in self.getDoValue(self.wd_do_content, './/oboInOwl:hasDbXref'):
            if not xref.text.split(":")[0] in self.xrefs.keys():
                self.xrefs[xref.text.split(":")[0]] = []
            self.xrefs[xref.text.split(":")[0]].append(xref.text.split(":")[1])
        
    def getDoValue(self, doClass, doNode):
        return doClass.findall(doNode, DiseaseOntology_settings.getDoNameSpaces())
                