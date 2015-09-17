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
import requests
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
        uniprotWikidataIds = dict()
        GeneSymbolWdMapping = dict()
        print "Getting all proteins with a uniprot ID in Wikidata"
        InWikiData = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[352]", "352")
        print "Getting all human gene symbols in Wikidata"
        GeneSymbolMapping = PBB_Core.WDItemList("CLAIM[279:7187] AND CLAIM[353] AND CLAIM[703:5]", "353")
        for geneSymbol in GeneSymbolMapping.wditems["props"]["353"]:
            GeneSymbolWdMapping[str(geneSymbol[2]).lower()] = geneSymbol[0]
        for proteinItem in InWikiData.wditems["props"]["352"]:
            uniprotWikidataIds[str(proteinItem[2])] = proteinItem[0]
        for uniprotWDQId in uniprotWikidataIds.keys():
          try:
            r = requests.get("http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f"+
                              str(uniprotWDQId)+
                              "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a++++++++%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09%09%3fgene+skos%3aprefLabel+%3fencodedBy+.%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b+%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%7b%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a++++++++%7b%3fupAlias+up%3ashortName+%3falias+.%7d%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fencodedBy+%3fplabel+%3fecName+%3fupversion&format=srj")

            # print r.text
            protein = json.loads(r.text)
            protein["logincreds"] = self.logincreds
            protein["wdid"] = 'Q'+str(uniprotWikidataIds[uniprotWDQId])
            # print protein
            protein["geneSymbols"] = GeneSymbolWdMapping
            proteinClass = human_protein(protein)

            
          except:
            # client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
            # client.captureException()
            print "There has been an except"
            print "Unexpected error:", sys.exc_info()[0]

            f = open('/tmp/exceptions.txt', 'a')
            # f.write("Unexpected error:", sys.exc_info()[0]+'\n')
            f.write(str(protein["results"]["bindings"][0]["uniprot"]["value"])+"\n")
            traceback.print_exc(file=f)
            f.close()
          
    def download_human_proteins(self):
        """
        Downloads the latest list of human proteins from uniprot through the URL specified in mygene_info_settings
        """
        print "Getting content from Uniprot"
        urllib.urlretrieve (mygene_info_settings.getUniprotUrl(), "human_proteins.json")
        file = open("human_proteins.json", 'r')
        return file.read()
        
class human_protein(object):
    def __init__(self, object):
        # Uniprot
        self.geneSymbols = object["geneSymbols"]
        self.logincreds = object["logincreds"]
        self.version = object["results"]["bindings"][0]["upversion"]["value"]
        self.wdid = object["wdid"]
        self.uniprot = object["results"]["bindings"][0]["uniprot"]["value"]
        print self.uniprot
        self.uniprotId = object["results"]["bindings"][0]["uniprot"]["value"].replace("http://purl.uniprot.org/uniprot/", "").replace(" ", "")
        self.name = object["results"]["bindings"][0]["plabel"]["value"]
        if "ecName" in object["results"]["bindings"][0].keys():
            print object["results"]["bindings"][0]["ecName"]["value"]
            self.ecname = object["results"]["bindings"][0]["ecName"]["value"]
        self.alias = []
        for syn in object["results"]["bindings"][0]["upalias"]["value"].split(";"):
            self.alias.append(syn)
        if "pdbid" in object["results"]["bindings"][0].keys():
         if object["results"]["bindings"][0]["pdbid"]["value"] != "":    
            self.pdb = []
            for pdbId in object["results"]["bindings"][0]["pdbid"]["value"].split(";"):
                self.pdb.append(pdbId.replace("http://rdf.wwpdb.org/pdb/", "").replace(" ", "")) 
        if "refseq" in object["results"]["bindings"][0].keys():
            self.refseq = []
            for refseqId in object["results"]["bindings"][0]["refseqid"]["value"].split(";"):
                self.refseq.append(refseqId.replace("http://purl.uniprot.org/refseq/", "").replace(" ", ""))
        self.ensemblp = []
        for ensP in object["results"]["bindings"][0]["ensemblp"]["value"].split(";"):
            self.ensemblp.append(ensP.replace("http://purl.uniprot.org/ensembl/", "").replace(" ", ""))
        self.encoded_by = []
        for encodedBy in object["results"]["bindings"][0]["encoded_by"]["value"].split(";"):
            self.encoded_by.append('q'+str(self.geneSymbols[str(encodedBy).lower()]))
            
        protein_reference = {
                            'ref_properties': [u'P143', 'TIMESTAMP'],
                            'ref_values': [u'Q905695' , 'TIMESTAMP']
                            } 
                            
        
                               
        # print vars(self)
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
        
        # P591 = EC number
        if "ecname" in vars(self):
            data2add["P591"] = [self.ecname]
            references['P591'] = [copy.deepcopy(protein_reference)]
        
        # P638 = PDBID
        if "pdb" in vars(self):
            print "len pdb = "+str(len(self.pdb))
            print self.pdb
            if len(self.pdb) > 0:
                data2add['P638'] = self.pdb
                references['P638'] = []
                data2add['P18'] = "http://www.rcsb.org/pdb/images/{}_bio_r_500.jpg".format{self.pdb}
                reference['P18'] = []
                for i in range(len(self.pdb)):
                    references['P638'].append(copy.deepcopy(protein_reference))
                    references['P18'].append(copy.deepcopy(protein_reference))

        # P637 = Refseq Protein ID            
        if "refseq" in vars(self):
            if len(self.refseq) > 0:
                data2add['P637'] = self.refseq
                references['P637'] = []
                for i in range(len(self.refseq)):
                    references['P637'].append(copy.deepcopy(protein_reference)) 
                    
        # P705 = Ensembl Protein ID
        if "ensemblp" in vars(self):
            if len(self.ensemblp) > 0: 
                 data2add['P705'] = self.ensemblp
                 references['P705'] = []
                 for i in range(len(self.ensemblp)):
                     references['P705'].append(copy.deepcopy(protein_reference)) 
        # P702 = Encoded by
        if "encoded_by" in vars(self):
            if len(self.encoded_by) > 0: 
                 data2add['P702'] = self.encoded_by
                 references['P702'] = []
                 for i in range(len(self.encoded_by)):
                     references['P702'].append(copy.deepcopy(protein_reference))
                     
                            
        wdPage = PBB_Core.WDItemEngine(wd_item_id=self.wdid, item_name=self.name, data=data2add, server="www.wikidata.org", references=references, domain="proteins")
        wdPage.set_aliases(aliases=self.alias, lang='en', append=True)
        wdPage.set_description(description='human protein', lang='en')
        self.wd_json_representation = wdPage.get_wd_json_representation() 
        PBB_Debug.prettyPrint(self.wd_json_representation)
        wdPage.write(self.logincreds)
        
        
    