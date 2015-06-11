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
        self.version_date = self.getDiseaseOntologyTimeStamp(self.content)
        for doClass in self.content.findall('.//owl:Class', DiseaseOntology_settings.getDoNameSpaces()):
            diseaseClass = disease(doClass)
            print diseaseClass.doID
    
    def download_disease_ontology(self):
        request = urllib2.Request(DiseaseOntology_settings.getdoUrl())
        u = urllib2.urlopen(request)
        do = u.read()
        return do
        
    def getDiseaseOntologyTimeStamp(self, diseaseOntology):
        doDate =  diseaseOntology.findall('.//oboInOwl:date', DiseaseOntology_settings.getDoNameSpaces())
        dateList = doDate[0].text.split(' ')[0].split(":")
        timeList = doDate[0].text.split(' ')[1].split(":")
        # return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+timeList[0]+":"+timeList[1]+":00Z"
        return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+"00:00:00Z"    
        
class  disease(object):
    def __init__(self, object):
        self.doContent = object
        self.doID = self.getDiseaseOntologyID(self.doContent)
        
    def getDiseaseOntologyID(self, doClass):
        return doClass.findall('.//oboInOwl:id', DiseaseOntology_settings.getDoNameSpaces())[0].text
        