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

class diseaseOntology():
    def __init__(self):  
        print self.download_disease_ontology()      
        self.content = ET.fromstring(self.download_disease_ontology())
        self.version_date = getDiseaseOntologyTimeStamp(self.content)
    
    def download_disease_ontology(self):
        namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
        dourl = 'http://purl.obolibrary.org/obo/doid.owl'
        request = urllib2.Request(dourl)
        u = urllib2.urlopen(request)
        do = u.read()
        
    def getDiseaseOntologyTimeStamp(self, diseaseOntology):
        doDate =  diseaseOntology.findall('.//oboInOwl:date', namespaces)
        dateList = doDate[0].text.split(' ')[0].split(":")
        timeList = doDate[0].text.split(' ')[1].split(":")
        # return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+timeList[0]+":"+timeList[1]+":00Z"
        return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+"00:00:00Z"    
        
