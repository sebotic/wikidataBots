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
import PBB_Core
import PBB_Debug
import urllib2
import xml.etree.cElementTree as ET
import sys
import DiseaseOntology_settings
import requests
try:
    import simplejson as json
except ImportError as e:
    import json
import PBB_login
import PBB_settings
import copy
import traceback

class diseaseOntology():
    def __init__(self):      
        counter = 0
        self.content = ET.fromstring(self.download_disease_ontology())
        self.version_date = self.getWDDiseaseOntologyTimeStamp()
        self.version_iri = self.getDiseaseOntologyVersionIRI()
        # self.wd_search_term = self.getWDSearchTerm()
        # updateDiseaseOntologyVersionInWD()
        self.updateDiseaseOntologyVersion()
        print self.doVersionID

        # Get all WikiData entries that contain a WikiData ID
        print "Getting all terms with a Disease Ontology ID in WikiData"
        doWikiData_id = dict()
        DoInWikiData = PBB_Core.WDItemList("CLAIM[699]", "699")
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

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
            
            print "do_id: "+diseaseClass.do_id
            print diseaseClass.wdid
            print diseaseClass.name
            print diseaseClass.synonyms
            print diseaseClass.xrefs
            counter = counter +1
          except:
              print "There has been an except"
              print "Unexpected error:", sys.exc_info()[0]

              f = open('/tmp/Diseaseexceptions.txt', 'a')
              # f.write("Unexpected error:", sys.exc_info()[0]+'\n')
              # f.write(diseaseClass.do_id+"\n")
              traceback.print_exc(file=f)
              f.close()

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
        return self.content.findall('.//owl:versionIRI', DiseaseOntology_settings.getDoNameSpaces())
        #for name, value in doversion[0].items():
        #    doUrlversion = value
        #return doUrlversion
    
    def addNewLabel(self, localdata, label):
        englishLabel = dict()
        englishLabel['language']='en'
        englishLabel['value']=label
        englishLabels=dict()
        englishLabels['en']=englishLabel
        localdata['entities']['labels']=englishLabels
        return localdata
        
    def addNewClaims(self, localdata, property, values, datatype, stated=True):
        localdata["entities"]["claims"][property] = []
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
            statement["references"]=self.addReference(statement["references"], 'P143', 5282129)
            localdata["entities"]["claims"][property].append(statement)
        return localdata  
        
    def addReference(self, references, property, itemId):
        found = False
        for ref in references:
          if property in ref["snaks"]:
            for snak in ref["snaks"][property]:
              if snak["datavalue"]["value"]["numeric-id"]==itemId:
                ref = setDateRetrievedTimestamp(ref)
                found = True
                break
        if not found:    
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
            reference = self.setDateRetrievedTimestamp(reference)
            references.append(reference)
        return references  
        
    def setDateRetrievedTimestamp(self, reference):
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
                login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
                cookies = login.get_edit_cookie()
                edit_token = login.get_edit_token()
                metadata={   u'entities': {   }}
                metadata["entities"]["claims"]=dict()
                metadata = self.addNewLabel(metadata, searchTerm)
                metadata = self.addNewClaims(metadata, 'P856', ["http://disease-ontology.org"], 'string', False) # official website P856
                metadata = self.addNewClaims(metadata, 'P1065', ["http://purl.obolibrary.org/obo/doid/releases/"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"/doid.owl"], 'string', False) # archive URL P1065
                
            
                headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'charset': 'utf-8'
                }
                payload = {
                    u'action': u'wbeditentity',
                    # u'data': json.dumps(self.wd_json_representation, encoding='utf-8'),
                    u'data': json.JSONEncoder(encoding='utf-8').encode(metadata['entities']),
                    u'new': 'item',
                    u'format': u'json',
                    u'token': edit_token
                }
                reply = requests.post('https://www.wikidata.org/w/api.php', headers=headers, data=payload, cookies=cookies)
                # pp.pprint(data)
                print reply.text
                self.doVersionID = json.loads(reply.text)['entity']['id']
                print "WikiData entry made for this version of Disease Ontology: "+self.doVersionID
        else:
            self.doVersionID = reply['search'][0]['id']
        print self.doVersionID
           
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
        # Reference section  
        doVersionID = object[1]
        doClass = object[0]         
        self.logincreds = object[3]
        self.wd_doMappings = object[4]
        
        self.wd_do_content = doClass
        PBB_Debug.prettyPrint(self.wd_do_content)
        self.do_id = self.getDoValue(self.wd_do_content, './/oboInOwl:id')[0].text
        self.name = self.getDoValue(self.wd_do_content, './/rdfs:label')[0].text
        classDescription = self.getDoValue(self.wd_do_content, './/oboInOwl:hasDefinition/oboInOwl:Definition/rdfs:label')
        if len(classDescription)>0:
            self.description = classDescription[0].text

        
        if self.do_id in object[2].keys():
            self.wdid = "Q"+str(object[2][self.do_id])
        else:
            self.wdid = None
            
        self.synonyms = []
        for synonym in self.getDoValue(self.wd_do_content, './/oboInOwl:hasExactSynonym'):
            self.synonyms.append(synonym.text)
        
        self.subclasses = []
        for subclass in self.getDoValue(self.wd_do_content, './/rdfs:subClassOf'):
            parts = subclass.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource').split("DOID_")
            print parts[1]
            if len(parts)>1:
                self.subclasses.append("DOID:"+parts[1])
        
        self.xrefs = dict()
        for xref in self.getDoValue(self.wd_do_content, './/oboInOwl:hasDbXref'):
            print xref.text
            if not xref.text.split(":")[0] in self.xrefs.keys():
                self.xrefs[xref.text.split(":")[0]] = []
            self.xrefs[xref.text.split(":")[0]].append(xref.text.split(":")[1])
        do_reference = {
                    'ref_properties': [u'P248', u'P143', 'TIMESTAMP'],
                    'ref_values': [doVersionID, u'Q5282129' , 'TIMESTAMP']
                }
        references = dict()
        data2add = dict()
        # Subclass of disease
        data2add["P279"] = ["12136"]
        references['P279'] = [copy.deepcopy(do_reference)]
        
        for subclass in self.subclasses:
            if subclass in self.wd_doMappings.keys():
                data2add["P279"].append(str(self.wd_doMappings[subclass]))
                references["P279"].append(copy.deepcopy(do_reference))
        #disease Ontology
        data2add["P699"] = [self.do_id]
        references["P699"] = [copy.deepcopy(do_reference)]
        
        if "Orphanet" in self.xrefs.keys():
            if isinstance(self.xrefs["Orphanet"], list): 
                data2add['P1550'] = self.xrefs["Orphanet"]
            else:
                data2add['P1550'] = [self.xrefs["Orphanet"]]
            if "P1550" not in references.keys():
                references["P1550"] = []
            for item in data2add['P1550']:
                references["P1550"].append(copy.deepcopy(do_reference))

        if "ICD10CM" in self.xrefs.keys():
            if isinstance(self.xrefs["ICD10CM"], list): 
                data2add['P494'] = self.xrefs["ICD10CM"]
            else:
                data2add['P494'] = [self.xrefs["ICD10CM"]]
            if "P494" not in references.keys():
                references["P494"] = []
            for item in data2add['P494']:
                references["P494"].append(copy.deepcopy(do_reference))

        if "ICD9CM" in self.xrefs.keys():
            if isinstance(self.xrefs["ICD9CM"], list): 
                data2add['P493'] = self.xrefs["ICD9CM"]
            else:
                data2add['P493'] = [self.xrefs["ICD9CM"]]
            if "P493" not in references.keys():
                references["P493"] = []
            for item in data2add['P493']:
                references["P493"].append(copy.deepcopy(do_reference))
            
        if "MSH" in self.xrefs.keys():
            if isinstance(self.xrefs["MSH"], list): 
                data2add['P486'] = self.xrefs["MSH"]
            else:
                data2add['P486'] = [self.xrefs["MSH"]]
            if "P486" not in references.keys():
                references["P486"] = []
            for item in data2add['P486']:
                references["P486"].append(copy.deepcopy(do_reference))

        if "NCI" in self.xrefs.keys():
            if isinstance(self.xrefs["NCI"], list): 
                data2add['P1748'] = self.xrefs["NCI"]
            else:
                data2add['P1748'] = [self.xrefs["NCI"]]
            if "P1748" not in references.keys():
                references["P1748"] = []
            for item in data2add['P1395']:
                references["P1748"].append(copy.deepcopy(do_reference))
           
        if "OMIM" in self.xrefs.keys():
            if isinstance(self.xrefs["OMIM"], list): 
                data2add['P492'] = self.xrefs["OMIM"]
            else:
                data2add['P492'] = [self.xrefs["OMIM"]]
            if "P492" not in references.keys():
                references["P492"] = []
            for item in data2add['P492']:
                references["P492"].append(copy.deepcopy(do_reference))
        print self.wdid
        if self.wdid != None: 
            wdPage = PBB_Core.WDItemEngine(self.wdid, self.name, data = data2add, server="www.wikidata.org", references=references)
            print self.wdid
            self.wd_json_representation = wdPage.get_wd_json_representation() 
            PBB_Debug.prettyPrint(self.wd_json_representation)
            wdPage.write(self.logincreds)

        
        
    def getDoValue(self, doClass, doNode):
        return doClass.findall(doNode, DiseaseOntology_settings.getDoNameSpaces())
        
     
                