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
import ProteinBoxBotKnowledge
import urllib
import urllib3
import certifi

import sys
import mygene_info_settings

try:
    import simplejson as json
except ImportError as e:
    import json
    
"""
This is the human-genome specific part of the ProteinBoxBot. Its purpose is to enrich Wikidata with
human gene and known external identifiers.
  
"""
    
class human_genome():
    def __init__(self):

        self.content = json.loads(self.download_human_genes())
        self.gene_count = self.content["total"]
        self.genes = self.content["hits"]
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        
        entrezWikidataIds = dict()
        print "Getting all entrez genes in Wikidata"
        InWikiData = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[351]", "351")
        for geneItem in InWikiData.wditems["props"]["351"]:
            entrezWikidataIds[str(geneItem[2])] = geneItem[0]
            
        for gene in self.genes:
            if str(gene["entrezgene"]) in entrezWikidataIds.keys():
               gene["wdid"] = 'Q'+str(entrezWikidataIds[str(gene["entrezgene"])])
            else:
               gene["wdid"] = None 
            
            geneClass = human_gene(gene)
            if str(geneClass.entrezgene) in entrezWikidataIds.keys():
                geneClass.wdid = 'Q'+str(entrezWikidataIds[str(geneClass.entrezgene)])
            else: 
                geneClass.wdid = None 
            if geneClass.wdid != None:
                print geneClass.wdid + " will be updated as Entrez "+ str(geneClass.entrezgene)
                PBB_Debug.prettyPrint(geneClass.wd_json_representation)
                print "adding "+str(geneClass.entrezgene) + " as statement"   

                    
                sys.exit()
            else:
                print str(geneClass.entrezgene) + " needs to be added to Wikidata"

    def download_human_genes(self):
        """
        Downloads the latest list of human genes from mygene.info through the URL specified in mygene_info_settings
        """
        # request = urllib2.Request(mygene_info_settings.getHumanGenesUrl())
        urllib.urlretrieve (mygene_info_settings.getHumanGenesUrl(), "human_genes.json")
        file = open("human_genes.json", 'r')
        return file.read()
        
class human_gene(object):
    def __init__(self, object):
        self.content = object
        self.entrezgene = object["entrezgene"]
        self.name = object["name"]
        self.symbol = object["symbol"]
        gene_annotations = json.loads(self.annotate_gene())
        print gene_annotations
        self.annotationstimestamp = gene_annotations["_timestamp"]
        self.wdid = object["wdid"]
        if "HGNC" in object:
            self.hgnc = object["HGNC"]
        else:
            self.hgnc = None
        if "ensembl" in object:
            if "gene" in object["ensembl"]:
                self.ensembl_gene = object["ensembl"]["gene"]
            else:
                self.ensembl_gene = None
            if "transcript" in object["ensembl"]:
                self.ensembl_transcript = object["ensembl"]["transcript"]
            else:
                self.ensembl_transcript = None
        if "homologene" in object:
            self.homologene = object["homologene"]["id"]
        else:
            self.homologene = None
        if "refseq" in object:
            if "rna" in object["refseq"]:
                self.refseq_rna = object["refseq"]["rna"]
            else :
                self.refseq_rna = None
                  
        data2add = dict()
        data2add["P279"] = ["7187"]
        data2add["P703"] = ["83310"]
        data2add['P351'] = [self.entrezgene]
        data2add['P353'] = [self.symbol]
        if "ensembl_gene" in vars(self):
            if self.ensembl_gene != None:
                data2add["P594"] = [self.ensembl_gene] 
        if "ensembl_gene" in vars(self):
            if self.ensembl_transcript != None:
                data2add['P704'] = [self.ensembl_transcript]        
        if "hgnc" in vars(self):
            if self.hgnc != None:
                data2add['P354'] = [self.hgnc]
        if "homologene" in vars(self):
            if self.homologene != None:
                data2add['P593'] = [self.homologene]
        if "refseq_rna" in vars(self):
            if self.refseq_rna != None:
                data2add['P639'] = [self.refseq_rna]        
        if "genomic_pos" in object: 
            if (isinstance(object["genomic_pos"], list)):
               chromosome = object["genomic_pos"][0]["chr"]
            else: chromosome = object["genomic_pos"]["chr"]
            data2add['P1057'] =  chromosomes[str(chromosome)]
            
            
        # Reference section           
        references = dict()
        references["P248"] = "Q17939676"
        references["P143"] = "Q20641742"
        
        
        if "alias" in gene_annotations.keys(): 
            self.synonyms = gene_annotations["alias"]
        else:
            self.synonyms = None
        if self.wdid != None:           
            wdPage = PBB_Core.WDItemEngine(self.wdid, self.name, False, data = data2add, server="www.wikidata.org", references=references)
            print self.wdid
            self.wd_json_representation = wdPage.get_wd_json_representation()   
        # else:
        #    wdPage = PBB_Core.WDItemEngine('', self.name, False, data = data2add, server="www.wikidata.org")
        

        
       

        ''' if "ensembl" in gene_annotations.keys():
            if "gene" in gene_annotations["ensembl"].keys():
                self.ensembl_gene = gene_annotations["ensembl"]["gene"]
            if "transcript" in gene_annotations["ensembl"].keys():
                self.ensembl_transcript = gene_annotations["ensembl"]["transcript"]
        '''        
        
    def annotate_gene(self):
        "Get gene annotations from mygene.info"
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        request = http.request("GET", mygene_info_settings.getGeneAnnotationsURL()+str(self.entrezgene))
        return request.data
        
        

        
        
        
        
        