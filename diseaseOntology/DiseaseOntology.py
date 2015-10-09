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

import time
import datetime
import sys
sys.path.append("/Users/andra/wikidatabots/ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import PBB_Debug
import xml.etree.cElementTree as ET
import sys
import DiseaseOntology_settings
import requests
try:
    import simplejson as json
except ImportError as e:
    import json
import copy
import traceback
from time import gmtime, strftime


class diseaseOntology():
    def __init__(self):      
        counter = 0
        self.content = ET.fromstring(self.download_disease_ontology())
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        # self.wd_search_term = self.getWDSearchTerm()
        # updateDiseaseOntologyVersionInWD()
        self.updateDiseaseOntologyVersion()

        # Get all WikiData entries that contain a WikiData ID
        print("Getting all terms with a Disease Ontology ID in WikiData")
        doWikiData_id = dict()
        DoInWikiData = PBB_Core.WDItemList("CLAIM[699]", "699")


        for diseaseItem in DoInWikiData.wditems["props"]["699"]:
           #print diseaseItem[2]
           doWikiData_id[str(diseaseItem[2])]=diseaseItem[0] # diseaseItem[2] = DO identifier, diseaseItem[0] = WD identifier
       
        for doClass in self.content.findall('.//owl:Class', DiseaseOntology_settings.getDoNameSpaces()):
          try:      
            disVars = []
            disVars.append(doClass)
            disVars.append(self.doVersionID)
            disVars.append(doWikiData_id)
            disVars.append(self.logincreds)
            disVars.append(doWikiData_id)
            
            diseaseClass = disease(disVars)          
            
            print("do_id: "+diseaseClass.do_id)
            print(diseaseClass.wdid)
            print(diseaseClass.name)
            print(diseaseClass.synonyms)
            print(diseaseClass.xrefs)
          except:
              f = open('/tmp/Diseaseexceptions.txt', 'a')
              # f.write("Unexpected error:", sys.exc_info()[0]+'\n')
              # f.write(diseaseClass.do_id+"\n")
              traceback.print_exc(file=f)
              f.close()

    def download_disease_ontology(self):
        """
        Downloads the latest version of disease ontology from the URL specified in DiseaseOntology_settings
        """
        r = requests.get(DiseaseOntology_settings.getdoUrl())
        return r.text

    def updateDiseaseOntologyVersion(self):   
        diseaseOntology = self.content   
        namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
        doDate =  diseaseOntology.findall('.//oboInOwl:date', namespaces)
        doversion = diseaseOntology.findall('.//owl:versionIRI', namespaces)      
        for name, value in doversion[0].items():
                    doUrlversion = value
        dateList = doDate[0].text.split(' ')[0].split(":")
        searchTerm = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]

        url = 'https://www.wikidata.org/w/api.php'
        params = {
            'action': 'wbsearchentities',
            'format' : 'json' , 
            'language' : 'en', 
            'type' : 'item', 
            'search': searchTerm
        }
        data = requests.get(url, params=params)
        reply = json.loads(data.text, "utf-8")     
        #PBB_Debug.prettyPrint(reply)
        self.doVersionID = None
        if len(reply['search']) == 0:
               data2add = []
               # official website
               data2add.append(PBB_Core.WDUrl(value="http://disease-ontology.org", prop_nr = "P856"))
               # archive URL
               githubURL = "https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/master/releases/"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"/doid.owl"
               data2add.append(PBB_Core.WDUrl(value=githubURL, prop_nr = "P1065"))
               doVersionPage = PBB_Core.WDItemEngine(item_name=searchTerm, data=data2add, server="www.wikidata.org", domain="disease")
               doVersionPage.set_description(description='Release of the Disease ontology', lang='en')
               PBB_Debug.prettyPrint(doVersionPage.get_wd_json_representation())
               self.doVersionID = doVersionPage.write(self.logincreds)
               print("WikiData entry made for this version of Disease Ontology: "+self.doVersionID)
        else:
            self.doVersionID = reply['search'][0]['id']
        print(self.doVersionID)
           

        
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
        # Reference section  
        doVersionID = object[1]
        doClass = object[0]         
        self.logincreds = object[3]
        self.wd_doMappings = object[4]
        
        self.wd_do_content = doClass
        PBB_Debug.prettyPrint(self.wd_do_content)
        self.do_id = self.getDoValue(self.wd_do_content, './/oboInOwl:id')[0].text
        print(self.do_id)
        self.name = self.getDoValue(self.wd_do_content, './/rdfs:label')[0].text
        print(self.name)
        classDescription = self.getDoValue(self.wd_do_content, './/oboInOwl:hasDefinition/oboInOwl:Definition/rdfs:label')
        if len(classDescription)>0:
            self.description = classDescription[0].text

        if self.do_id in object[2].keys():
            self.wdid = "Q"+str(object[2][self.do_id])
        else:
            self.wdid = None

        if self.getDoValue(self.wd_do_content, './/owl:deprecated') == "true":
            self.rank = "deprecated"
        else:
            self.rank = "normal"
            
        self.synonyms = []
        for synonym in self.getDoValue(self.wd_do_content, './/oboInOwl:hasExactSynonym'):
            self.synonyms.append(synonym.text)
        
        self.subclasses = []
        for subclass in self.getDoValue(self.wd_do_content, './/rdfs:subClassOf'):
            parts = subclass.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource').split("DOID_")
            if len(parts)>1:
                self.subclasses.append("DOID:"+parts[1])
        
        self.xrefs = dict()
        for xref in self.getDoValue(self.wd_do_content, './/oboInOwl:hasDbXref'):
            if not xref.text.split(":")[0] in self.xrefs.keys():
                self.xrefs[xref.text.split(":")[0]] = []
            self.xrefs[xref.text.split(":")[0]].append(xref.text.split(":")[1])

        refStatedIn = PBB_Core.WDItemID(value=doVersionID, prop_nr='P248', is_reference=True)
        refImported = PBB_Core.WDItemID(value='Q5282129', prop_nr='P143', is_reference=True)
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        do_reference = [refStatedIn, refImported, refRetrieved]

        prep = dict()
        prep["P279"] = [PBB_Core.WDItemID(value='Q12136', prop_nr='P279', references=[copy.deepcopy(do_reference)])]
        # Subclass of disease
        for subclass in self.subclasses:
            if subclass in self.wd_doMappings.keys():
                prep["P279"].append(PBB_Core.WDItemID(value=self.wd_doMappings[subclass], prop_nr='P279', references=[copy.deepcopy(do_reference)]))


        if "Orphanet" in self.xrefs.keys():
            if isinstance(self.xrefs["Orphanet"], list):
                for id in self.xrefs["Orphanet"]:
                    prep["P1550"].append(PBB_Core.WDString(value=self.xrefs["Orphanet"], prop_nr='P1550', references=[copy.deepcopy(do_reference)]))
            else:
                prep["P1550"] = [PBB_Core.WDString(value=self.xrefs["Orphanet"], prop_nr='P1550', references=[copy.deepcopy(do_reference)])]

        #disease Ontology

        prep["P699"] = [PBB_Core.WDString(value=self.do_id, prop_nr='P699', references=[do_reference], rank=self.rank)]

        if "url" in self.xrefs.keys():
            if "//en.wikipedia.org/wiki/" in self.xrefs["url"]:
                wikilink = self.xrefs["url"].replace("//en.wikipedia.org/wiki/", "").replace("_", "")
            else:
                wikilink = None
        else:
            wikilink = None


        if "ICD10CM" in self.xrefs.keys():
            if isinstance(self.xrefs["ICD10CM"], list):
                for id in self.xrefs["ICD10CM"]:
                    prep["P494"].append(PBB_Core.WDString(value=self.xrefs["ICD10CM"], prop_nr='P494', references=[copy.deepcopy(do_reference)]))
            else:
                prep["P494"] = [PBB_Core.WDString(value=self.xrefs["ICD10CM"], prop_nr='P494', references=[copy.deepcopy(do_reference)])]

        if "ICD9CM" in self.xrefs.keys():
            if isinstance(self.xrefs["ICD9CM"], list):
                for id in self.xrefs["ICD9CM"]:
                    prep["P493"].append(PBB_Core.WDString(value=self.xrefs["ICD9CM"], prop_nr='P493', references=[copy.deepcopy(do_reference)]))
            else:
                prep["P493"] = [PBB_Core.WDString(value=self.xrefs["ICD9CM"], prop_nr='P493', references=[copy.deepcopy(do_reference)])]

        if "MSH" in self.xrefs.keys():
            if isinstance(self.xrefs["MSH"], list):
                for id in self.xrefs["MSH"]:
                    prep["P486"].append(PBB_Core.WDString(value=self.xrefs["MSH"], prop_nr='P486', references=[copy.deepcopy(do_reference)]))
            else:
                prep["P486"] = [PBB_Core.WDString(value=self.xrefs["MSH"], prop_nr='P486', references=[copy.deepcopy(do_reference)])]

        if "NCI" in self.xrefs.keys():
            if isinstance(self.xrefs["NCI"], list):
                for id in self.xrefs["NCI"]:
                    prep["P1748"].append(PBB_Core.WDString(value=self.xrefs["NCI"], prop_nr='P1748', references=[copy.deepcopy(do_reference)]))
            else:
                prep["P1748"] = [PBB_Core.WDString(value=self.xrefs["NCI"], prop_nr='P1748', references=[copy.deepcopy(do_reference)])]

        if "OMIM" in self.xrefs.keys():
            if isinstance(self.xrefs["OMIM"], list):
                for id in self.xrefs["OMIM"]:
                    prep["P492"].append(PBB_Core.WDString(value=self.xrefs["OMIM"], prop_nr='P492', references=[copy.deepcopy(do_reference)]))
            else:
                prep["492"] = [PBB_Core.WDString(value=self.xrefs["OMIM"], prop_nr='P492', references=[copy.deepcopy(do_reference)])]

        print(self.wdid)
        data2add = []
        for key in prep.keys():
            for statement in prep[key]:
                data2add.append(statement)
                print(statement.prop_nr, statement.value)

        if self.wdid is not None:
            wdPage = PBB_Core.WDItemEngine(self.wdid, item_name=self.name, data=data2add, server="www.wikidata.org", domain="diseases")
        else:
            wdPage = PBB_Core.WDItemEngine(item_name=self.name, data=data2add, server="www.wikidata.org", domain="diseases")

        wdPage.set_description(description='Human disease', lang='en')
        if wikilink is not None:
            wdPage.set_sitelink(site="enwiki", title = wikilink)
        if self.synonyms is not None:
             wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
        self.wd_json_representation = wdPage.get_wd_json_representation()
        PBB_Debug.prettyPrint(self.wd_json_representation)
        wdPage.write(self.logincreds)

        
    def getDoValue(self, doClass, doNode):
        return doClass.findall(doNode, DiseaseOntology_settings.getDoNameSpaces())
        
     
                