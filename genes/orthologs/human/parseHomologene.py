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

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings
import copy


class orthologClass(object):
    def __init__(self, object):
        self.logincreds = object["logincreds"]
        self.source = object["source"]
        self.ortholog = object["ortholog"]
        self.species = object["speciesWdID"]
        homologene_reference = {
                    'ref_properties': [u'P248', u'P143', 'TIMESTAMP'],
                    'ref_values': [u'Q20976936', u'Q468215' , 'TIMESTAMP']
                }
            
        references = dict()
        data2add = dict()
        data2add["P684"] = [self.ortholog]
        references['P684'] = [copy.deepcopy(homologene_reference)]
        
        wdPage = PBB_Core.WDItemEngine(wd_item_id=self.source, data=data2add, server="www.wikidata.org", references=references, domain="genes")
        wdPage.write(self.logincreds)

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

humanEntrezWikidataIds = dict()
mouseEntrezWikidataIds = dict()

print "Getting all human genes in Wikidata"
InWikiData = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[351]", "351")
for geneItem in InWikiData.wditems["props"]["351"]:
    humanEntrezWikidataIds[str(geneItem[2])] = geneItem[0]

print "Getting all mouse genes in Wikidata"
InWikiData = PBB_Core.WDItemList("CLAIM[703:83310] AND CLAIM[351]", "351")
for geneItem in InWikiData.wditems["props"]["351"]:
    mouseEntrezWikidataIds[str(geneItem[2])] = geneItem[0]
    
homologene = open("/tmp/homologene.data", "r")
humanOrthologs = dict()
mouseOrthologs = dict()

for line in homologene:
    for line in homologene:
        fields = line.split('\t')
        if fields[1]=="9606":
            humanOrthologs[fields[0]] = fields[2]
        if fields[1]=="10090":
            mouseOrthologs[fields[0]] = fields[2]

for ortholog in humanOrthologs.keys():
    if ortholog in mouseOrthologs.keys():
        if ((humanOrthologs[ortholog] in humanEntrezWikidataIds.keys()) and
           (mouseOrthologs[ortholog] in mouseEntrezWikidataIds.keys())) :
            print "{} \t {} \tQ{}) \t {} \tQ{}".format(ortholog, humanOrthologs[ortholog], humanEntrezWikidataIds[humanOrthologs[ortholog]], 
                                                mouseOrthologs[ortholog], mouseEntrezWikidataIds[mouseOrthologs[ortholog]])
            humanOrtholog = dict()
            mouseOrtholog = dict()
            humanOrtholog["logincreds"] = logincreds
            mouseOrtholog["logincreds"] = logincreds
            humanOrtholog["ortholog"] = "Q"+str(humanEntrezWikidataIds[humanOrthologs[ortholog]])
            humanOrtholog["speciesWdID"] = "Q5"
            humanOrtholog["source"] = "Q"+str(mouseEntrezWikidataIds[mouseOrthologs[ortholog]])
            HumanOrthoLogClass = orthologClass(humanOrtholog)
            mouseOrtholog["ortholog"] = "Q"+str(mouseEntrezWikidataIds[mouseOrthologs[ortholog]])
            mouseOrtholog["speciesWdID"] = "Q83310"
            mouseOrtholog["source"] = "Q"+str(humanEntrezWikidataIds[humanOrthologs[ortholog]]) 
            MouseOrthoLogClass = orthologClass(mouseOrtholog)     
              
                                        
    
    
	