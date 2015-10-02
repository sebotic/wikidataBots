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
import requests
import copy
import traceback
import mygene_info_settings
from time import gmtime, strftime


try:
    import simplejson as json
except ImportError as e:
    import json
    
"""
This is the human-genome specific part of the ProteinBoxBot. Its purpose is to enrich Wikidata with
human gene and known external identifiers.
  
"""
    
class genome(object):
    def __init__(self, object):
        counter = 0
        self.genomeInfo = object
        print("Getting all {} genes in Wikidata".format(self.genomeInfo["name"]))
        self.content = self.download_genes(self.genomeInfo["name"])
        self.gene_count = self.content["total"]
        self.genes = self.content["hits"]
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

        entrezWikidataIds = dict()
        wdqQuery = "CLAIM[703:{}] AND CLAIM[351]".format(self.genomeInfo["wdid"].replace("Q", ""))
        InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")
        '''
        Below a mapping is created between entrez gene ids and wikidata identifiers.
        '''
        for geneItem in InWikiData.wditems["props"]["351"]:
            entrezWikidataIds[str(geneItem[2])] = geneItem[0]

        for gene in self.genes:
          try:         
                if str(gene["entrezgene"]) in entrezWikidataIds.keys():
                   gene["wdid"] = 'Q'+str(entrezWikidataIds[str(gene["entrezgene"])])
                else:
                   gene["wdid"] = None 
                gene["logincreds"] = self.logincreds
                gene["genomeInfo"] = self.genomeInfo
                geneClass = mammal_gene(gene)
                if str(geneClass.entrezgene) in entrezWikidataIds.keys():
                    geneClass.wdid = 'Q'+str(entrezWikidataIds[str(geneClass.entrezgene)])
                else: 
                    geneClass.wdid = None 
                counter = counter +1
                if counter == 100:
                    self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
                
          except:
              f = open('/tmp/exceptions_{}.txt'.format(self.genomeInfo["name"]), 'a')
              f.write(str(gene["entrezgene"])+"\n")
              # f.write()
              traceback.print_exc(file=f)
              f.close()
              

    def download_genes(self, species):
        """
        Downloads the latest list of human genes from mygene.info through the URL specified in mygene_info_settings
        """
        print(mygene_info_settings.getGenesUrl().format(species))
        r = requests.get(mygene_info_settings.getGenesUrl().format(species))
        return r.json()
        
class mammal_gene(object):
    def __init__(self, object):
        self.genomeInfo = object["genomeInfo"]
        self.content = object
        self.entrezgene = object["entrezgene"]
        self.name = object["name"]
        self.logincreds = object["logincreds"]
        gene_annotations = self.annotate_gene()

        self.annotationstimestamp = gene_annotations["_timestamp"]
        self.wdid = object["wdid"]
        
        # symbol:
        self.symbol = object["symbol"]
        
        # HGNC
        if "HGNC" in gene_annotations:
            if isinstance(gene_annotations["HGNC"], list): 
                self.hgnc = gene_annotations["HGNC"]
            else:
                self.hgnc = [gene_annotations["HGNC"]]
        else:
            self.hgnc = None
            
        # Ensembl Gene & transcript
        if "ensembl" in gene_annotations:
            if "gene" in gene_annotations["ensembl"]:
                if isinstance(gene_annotations["ensembl"]["gene"], list): 
                    self.ensembl_gene = gene_annotations["ensembl"]["gene"]
                else:
                    self.ensembl_gene = [gene_annotations["ensembl"]["gene"]]
            else:
                self.ensembl_gene = None
            
            if "transcript" in gene_annotations["ensembl"]:
                if isinstance(gene_annotations["ensembl"]["transcript"], list): 
                    self.ensembl_transcript = gene_annotations["ensembl"]["transcript"]
                else:
                    self.ensembl_transcript = [gene_annotations["ensembl"]["transcript"]]
            else:
                self.ensembl_transcript = None
        # Homologene
        if "homologene" in gene_annotations:
            if isinstance(gene_annotations["homologene"]["id"], list): 
                self.homologene = [str(i) for i in gene_annotations["homologene"]["id"]]
            else:
                self.homologene = [str(gene_annotations["homologene"]["id"])]
        else:
            self.homologene = None
        # Refseq 
        if "refseq" in gene_annotations:
            if "rna" in gene_annotations["refseq"]:
                if isinstance(gene_annotations["refseq"]["rna"], list): 
                    self.refseq_rna = gene_annotations["refseq"]["rna"]
                else:
                    self.refseq_rna = [gene_annotations["refseq"]["rna"]]
            else :
                self.refseq_rna = None
        else :
            self.refseq_rna = None 
         
         # MGI
        if "MGI" in gene_annotations:
             if isinstance(gene_annotations["MGI"], list): 
                 self.MGI = gene_annotations["MGI"]
             else:
                 self.MGI = [gene_annotations["MGI"]]
        else:
             self.MGI = None
             
        self.chromosome = None
        self.startpost = None
        self.endpos = None          
        if "genomic_pos" in gene_annotations:
            if (isinstance(gene_annotations["genomic_pos"], list)): 
                self.chromosome = []
                self.startpos = []
                self.endpos = [] 
                for i in range(len(gene_annotations["genomic_pos"])):
                    if gene_annotations["genomic_pos"][i]["chr"] in ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]].keys():
                           self.chromosome.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][gene_annotations["genomic_pos"][i]["chr"]])
                           self.startpos.append(gene_annotations["genomic_pos"][i]["start"])
                           self.endpos.append(gene_annotations["genomic_pos"][i]["end"])
            else:
                self.chromosome = []
                self.startpos = []
                self.endpos = []
                if gene_annotations["genomic_pos"]["chr"] in ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]].keys():
                       self.chromosome.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][gene_annotations["genomic_pos"]["chr"]])
                       self.startpos.append(gene_annotations["genomic_pos"]["start"])
                       self.endpos.append(gene_annotations["genomic_pos"]["end"])     
        
        # type of Gene
        if "type_of_gene" in gene_annotations:
            self.type_of_gene = []
            if gene_annotations["type_of_gene"]=="ncRNA":
                self.type_of_gene.append("Q427087")
            if gene_annotations["type_of_gene"]=="snRNA":
                self.type_of_gene.append("Q284578") 
            if gene_annotations["type_of_gene"]=="snoRNA":
                self.type_of_gene.append("Q284416")
            if gene_annotations["type_of_gene"]=="rRNA":
                self.type_of_gene.append("Q215980")
            if gene_annotations["type_of_gene"]=="tRNA":
                self.type_of_gene.append("Q201448")
            if gene_annotations["type_of_gene"]=="pseudo":
                self.type_of_gene.append("Q277338") 
            if gene_annotations["type_of_gene"]=="protein-coding":
                self.type_of_gene.append("Q20747295")                          
        else:
            self.type_of_gene = None
        # Reference section  
        # Prepare references
        refStatedIn = PBB_Core.WDItemID(value=self.genomeInfo["release"], prop_nr='P248', is_reference=True)
        refImported = PBB_Core.WDItemID(value='Q20641742', prop_nr='P143', is_reference=True)
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        gene_reference =  [[refStatedIn, refImported, refRetrieved]]
        
        genomeBuildQualifier = PBB_Core.WDItemID(value=self.genomeInfo["genome_assembly"], prop_nr='P659', is_qualifier=True)
        prep = dict()           
        prep['P279'] = [PBB_Core.WDItemID(value="Q7187", prop_nr='P279', references=gene_reference)]
        prep['P703'] = [PBB_Core.WDItemID(value=self.genomeInfo["wdid"], prop_nr='P703', references=gene_reference)]
        prep['P353'] = [PBB_Core.WDString(value=self.symbol, prop_nr='P353', references=gene_reference)]   
        prep['P351'] = [PBB_Core.WDString(value=str(self.entrezgene), prop_nr='P351', references=gene_reference)]
        prep["P279"] = []
        prep['P279'].append(PBB_Core.WDItemID(value="Q7187", prop_nr='P279', references=gene_reference))
        if "type_of_gene" in vars(self):
            if self.type_of_gene != None:
                for i in range(len(self.type_of_gene)):
                    prep['P279'].append(PBB_Core.WDItemID(value=self.type_of_gene[i], prop_nr='P279', references=gene_reference))
                    
        if "ensembl_gene" in vars(self):
            if self.ensembl_gene != None:
                prep['P594'] = []
                for ensemblg in self.ensembl_gene:
                    prep['P594'].append(PBB_Core.WDString(value=ensemblg, prop_nr='P594', references=gene_reference))
   
        if "ensembl_transcript" in vars(self):
            if self.ensembl_transcript != None:
                prep['P704'] = []
                for ensemblt in self.ensembl_transcript:
                    prep['P704'].append(PBB_Core.WDString(value=ensemblt, prop_nr='P704', references=gene_reference))
                    
        if "hgnc" in vars(self):
            if self.hgnc != None:
                prep['P354'] = []
                for hugo in self.hgnc:
                    prep['P354'].append(PBB_Core.WDString(value=hugo, prop_nr='P354', references=gene_reference))
                
        if "homologene" in vars(self):
            if self.homologene != None:
                prep['P593'] = []
                for ortholog in self.homologene:
                    prep['P593'].append(PBB_Core.WDString(value=ortholog, prop_nr='P593', references=gene_reference))

        if "refseq_rna" in vars(self):
            if self.refseq_rna != None:
                prep['P639'] = []
                for refseq in self.refseq_rna:
                    prep['P639'].append(PBB_Core.WDString(value=refseq, prop_nr='P639', references=gene_reference))

        if "chromosome" in vars(self):
            prep['P1057'] = []
            if self.chromosome != None:
                for chrom in list(set(self.chromosome)):
                     prep['P1057'].append(PBB_Core.WDItemID(value=chrom, prop_nr='P1057', references=gene_reference))
            
        if "startpos" in vars(self):
            prep['P644'] = [] 
            if self.startpos != None:
                for pos in self.startpos:
                    prep['P644'].append(PBB_Core.WDString(value=str(pos), prop_nr='P644', references=gene_reference,
                                                          qualifiers=[copy.deepcopy(genomeBuildQualifier)]))
        if "endpos" in vars(self):
            prep['P645'] = [] 
            if self.endpos != None:
                for pos in self.endpos:
                    prep['P645'].append(PBB_Core.WDString(value=str(pos), prop_nr='P645', references=gene_reference,
                                                          qualifiers=[copy.deepcopy(genomeBuildQualifier)]))
                              
        if "MGI" in vars(self):
            prep['P671'] = []
            if self.MGI != None:
                for mgi in self.MGI:
                    prep['P671'].append(PBB_Core.WDString(value=mgi, prop_nr='P671'), references=gene_reference)
        
        if "alias" in gene_annotations.keys():
            if isinstance(gene_annotations["alias"], list):
                self.synonyms = []
                for alias in gene_annotations["alias"]:
                    self.synonyms.append(alias)
            else:
               self.synonyms = [gene_annotations["alias"]]
            self.synonyms.append(self.symbol)
            print(self.synonyms)
        else:
            self.synonyms = None
            
        data2add = []
        for key in prep.keys():
            for statement in prep[key]:
                data2add.append(statement)
                print(statement.prop_nr, statement.value)
             
        if self.wdid != None:   
            wdPage = PBB_Core.WDItemEngine(self.wdid, self.name, data = data2add, server="www.wikidata.org", domain="genes")
            wdPage.set_description(description=self.genomeInfo['name']+' gene', lang='en')
            if self.synonyms != None:
                wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
            print(self.wdid)
            self.wd_json_representation = wdPage.get_wd_json_representation()
            PBB_Debug.prettyPrint(self.wd_json_representation) 
            PBB_Debug.prettyPrint(data2add)
            # print(self.wd_json_representation)
            wdPage.write(self.logincreds)
        else:
            wdPage = PBB_Core.WDItemEngine(item_name=self.name, data=data2add, server="www.wikidata.org", domain="genes")
            wdPage.set_description(description=self.genomeInfo['name']+' gene', lang='en')
            if self.synonyms != None:
                wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
            self.wd_json_representation = wdPage.get_wd_json_representation() 
            PBB_Debug.prettyPrint(self.wd_json_representation)
            PBB_Debug.prettyPrint(data2add)
            # print(self.wd_json_representation)
            wdPage.write(self.logincreds)
               
    def annotate_gene(self):
        # "Get gene annotations from mygene.info"     
        r = requests.get(mygene_info_settings.getGeneAnnotationsURL()+str(self.entrezgene))
        return r.json()
        # return request.data
        
        
 
        
        
        
        
        