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

import urllib2
import xml.etree.cElementTree as ET
import sys
import DiseaseOntology_settings

class diseaseOntology():
    def __init__(self):      
        self.content = ET.fromstring(self.download_disease_ontology())
        self.version_date = self.getWDDiseaseOntologyTimeStamp(self.content)
        self.version_iri = self.getDiseaseOntologyVersionIRI(self.content)
        self.wd_search_term = self.getWDSearchTerm(self.content)
        # updateDiseaseOntologyVersionInWD()
        for doClass in self.content.findall('.//owl:Class', DiseaseOntology_settings.getDoNameSpaces()):
            diseaseClass = disease(doClass)
            print diseaseClass.doID
            print diseaseClass.label
    
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
        
    def getWDDiseaseOntologyTimeStamp(self):
        """
        Converts a Disease Ontology version date to the format recognized by WikiData
        """
        doDate = getDiseaseOntologyTimeStamp()
        dateList = doDate[0].text.split(' ')[0].split(":")
        timeList = doDate[0].text.split(' ')[1].split(":")
        return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+"00:00:00Z"  
    
    def getDiseaseOntologyVersionIRI(self):
        """
        Extracts the URL from where the disease ontology version applicable
        """
        doVersion = self.content.findall('.//owl:versionIRI', DiseaseOntology_settings.getDoNameSpaces()
        for name, value in doversion[0].items():
                    doUrlversion = value
        return doUrlversion
            
    def updateDiseaseOntologyVersionInWD(self):
        pass
        
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
        self.do_id = self.getDoValue(self.doContent, './/oboInOwl:id')[0].text
        self.label = self.getDoValue(self.doContent, './/rdfs:label')[0].text
        self.synonyms = self.getDoValue(self.doContent, './/oboInOwl:hasExactSynonym')
        self.xrefs = dict()
        for xref in self.getDoValue(self.doContent, './/oboInOwl:hasDbXref'):
            if not xref.text.split(":")[0] in self.xrefs.keys():
                self.xrefs[xref.text.split(":")[0]] = []
            self.xrefs[xref.text.split(":")[0]].append(xref.text.split(":")[1])
        
    def getDoValue(self, doClass, doNode):
        return doClass.findall(doNode, DiseaseOntology_settings.getDoNameSpaces())
                