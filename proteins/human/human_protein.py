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
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
import PBB_Functions
import urllib
import urllib3
import certifi
import copy
import traceback
import sys
import mygene_info_settings
from SPARQLWrapper import SPARQLWrapper

from raven import Client

try:
    import simplejson as json
except ImportError as e:
    import json
	
class human_proteome():
    def __init__(self):
        self.content = json.loads(self.download_human_proteins())
        # print self.content["results"]["bindings"]
        self.protein_count = len(self.content["results"]["bindings"])
        self.proteins = self.content["results"]["bindings"]
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        
        for protein in self.proteins:
            print protein
            try:
                protein["logincreds"] = self.logincreds
                proteinClass = human_protein(protein)
                break
            except:
                # client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
                # client.captureException()
                print "There has been an except"
                print "Unexpected error:", sys.exc_info()[0]

                f = open('/tmp/exceptions.txt', 'a')
                # f.write("Unexpected error:", sys.exc_info()[0]+'\n')
                f.write(str(protein["uniprot"]["value"])+"\n")
                traceback.print_exc(file=f)
                f.close()
          
    def download_human_proteins(self):
        """
        Downloads the latest list of human proteins from uniprot through the URL specified in mygene_info_settings
        """
        print "Getting proteins from Uniprot"
        urllib.urlretrieve (mygene_info_settings.getUniprotUrl(), "human_proteins.json")
        file = open("human_proteins.json", 'r')
        return file.read()
        
class human_protein(object):
    def __init__(self, object):
        # Uniprot
        self.logincreds = object["logincreds"]
        self.version = object["upversion"]["value"]
        self.wdid = object["wd_url"]["value"].replace("http://www.wikidata.org/entity/","").replace(" ", "")
        self.uniprot = object["uniprot"]["value"]
        self.uniprotId = object["uniprot"]["value"].replace("http://purl.uniprot.org/uniprot/", "").replace(" ", "")
        self.name = object["proteinLabel"]["value"]
        self.pdb = []
        for pdbId in object["pdbId"]["value"].split(";"):
            self.pdb.append(pdbId.replace("http://rdf.wwpdb.org/pdb/", "").replace(" ", "")) 
        self.refseq = []
        for refseqId in object["RefSeq_Id"]["value"].split(";"):
            self.refseq.append(refseqId.replace("http://purl.uniprot.org/refseq/", "").replace(" ", ""))
        
        '''protein_reference = {
                    'ref_properties': [u'P854', u'P143', 'TIMESTAMP'],
                    'ref_values': ['http://www.uniprot.org/uniprot/'+self.uniprotId+'.txt?version='+self.version, u'Q905695' , 'TIMESTAMP']
                }'''
        protein_reference = {
                            'ref_properties': [u'P143', 'TIMESTAMP'],
                            'ref_values': [u'Q905695' , 'TIMESTAMP']
                        }        
        
        references = dict()
        data2add = dict()
        
        # P279 = subclass of
        data2add["P279"] = ["8054"]
        references['P279'] = [copy.deepcopy(protein_reference)]
        
        # P703 = found in taxon
        data2add["P703"] = ["5"]
        references['P703'] = [copy.deepcopy(protein_reference)]
        
        # P352 = UniprotID
        data2add["P352"] = [self.uniprotId]
        references['P352'] = [copy.deepcopy(protein_reference)]
        
        # P638 = PDBID
        if "pdb" in vars(self):
            if self.pdb != None:
                data2add['P638'] = self.pdb
                references['P638'] = []
                for i in range(len(self.pdb)):
                    references['P638'].append(copy.deepcopy(protein_reference))

        # P637 = Refseq Protein ID            
        if "refseq" in vars(self):
            if self.refseq != None:
                data2add['P637'] = self.refseq
                references['P637'] = []
                for i in range(len(self.refseq)):
                    references['P637'].append(copy.deepcopy(protein_reference))            
        wdPage = PBB_Core.WDItemEngine(wd_item_id=self.wdid, item_name=self.name, data=data2add, server="www.wikidata.org", references=references, domain="proteins")
        self.wd_json_representation = wdPage.get_wd_json_representation() 
        PBB_Debug.prettyPrint(self.wd_json_representation)
        wdPage.write(self.logincreds)
        
    