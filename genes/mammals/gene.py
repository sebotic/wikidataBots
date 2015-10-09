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

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
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
from SPARQLWrapper import SPARQLWrapper, JSON

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

        sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")

        print("Getting all molecular functions in Wikidata")
        sparql.setQuery("""
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX v: <http://www.wikidata.org/prop/statement/>
            SELECT DISTINCT ?mf ?mfLabel WHERE {
                ?a p:P680/v:P680 ?mf .
                ?mf rdfs:label ?mfLabel .
                FILTER (LANG(?mfLabel) = 'en')
            }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        PBB_Debug.prettyPrint(results)
        mfWikidataIds = dict()
        for result in results["results"]["bindings"]:
            mfWikidataIds[result["mfLabel"]["value"]] = result["mf"]["value"].replace("http://www.wikidata.org/entity/",
                                                                                      "")
        PBB_Debug.prettyPrint(mfWikidataIds)

        print("Getting all cell components in Wikidata")
        sparql.setQuery("""
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX v: <http://www.wikidata.org/prop/statement/>
            SELECT DISTINCT ?cc ?ccLabel WHERE {
                ?a p:P681/v:P681 ?cc .
                ?cc rdfs:label ?ccLabel .
                FILTER (LANG(?ccLabel) = 'en')
            }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        PBB_Debug.prettyPrint(results)
        ccWikidataIds = dict()
        for result in results["results"]["bindings"]:
            ccWikidataIds[result["ccLabel"]["value"]] = result["cc"]["value"].replace("http://www.wikidata.org/entity/",
                                                                                      "")
        PBB_Debug.prettyPrint(ccWikidataIds)

        print("Getting all biological process in Wikidata")
        sparql.setQuery("""
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX v: <http://www.wikidata.org/prop/statement/>
            SELECT DISTINCT ?bp ?bpLabel WHERE {
                ?a p:P682/v:P682 ?bp .
                ?bp rdfs:label ?bpLabel .
                FILTER (LANG(?bpLabel) = 'en')
            }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        PBB_Debug.prettyPrint(results)
        bpWikidataIds = dict()
        for result in results["results"]["bindings"]:
            bpWikidataIds[result["bpLabel"]["value"]] = result["bp"]["value"].replace("http://www.wikidata.org/entity/",
                                                                                      "")
        PBB_Debug.prettyPrint(bpWikidataIds)

        for gene in self.genes:
            try:
                if str(gene["entrezgene"]) in entrezWikidataIds.keys():
                    gene["wdid"] = 'Q' + str(entrezWikidataIds[str(gene["entrezgene"])])
                else:
                    gene["wdid"] = None
                gene["logincreds"] = self.logincreds
                gene["genomeInfo"] = self.genomeInfo
                gene["biological_process"] = bpWikidataIds
                gene["cell_component"] = ccWikidataIds
                gene["molecular_function"] = mfWikidataIds
                geneClass = mammal_gene(gene)
                if str(geneClass.entrezgene) in entrezWikidataIds.keys():
                    geneClass.wdid = 'Q' + str(entrezWikidataIds[str(geneClass.entrezgene)])
                else:
                    geneClass.wdid = None
                counter = counter + 1
                if counter == 100:
                    self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(),
                                                        PBB_settings.getWikiDataPassword())

            except:
                f = open('/tmp/exceptions_{}.txt'.format(self.genomeInfo["name"]), 'a')
                f.write(str(gene["entrezgene"]) + "\n")
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
        """

        :type self: object
        """
        self.genomeInfo = object["genomeInfo"]
        self.content = object
        self.entrezgene = object["entrezgene"]
        self.name = object["name"]
        self.logincreds = object["logincreds"]
        gene_annotations = self.annotate_gene()
        self.molecular_function_index = object["molecular_function"]
        self.cell_componenent_index = object["cell_component"]
        self.biological_process_index = object["biological_process"]

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

        # GO
        if "go" in gene_annotations:
            if "BP" in gene_annotations["go"]:
                # P682
                if isinstance(gene_annotations["go"]["BP"], list):
                    self.biological_process = gene_annotations["go"]["BP"]
                else:
                    self.biological_process = [gene_annotations["go"]["BP"]]
            else:
                self.biological_process = None
            if "CC" in gene_annotations["go"]:
                if isinstance(gene_annotations["go"]["CC"], list):
                    self.cell_componenent = gene_annotations["go"]["CC"]
                else:
                    self.cell_componenent = [gene_annotations["go"]["CC"]]
            else:
                self.cell_componenent = None
            if "MF" in gene_annotations["go"]:
                # P680
                if isinstance(gene_annotations["go"]["MF"], list):
                    self.molecular_function = gene_annotations["go"]["MF"]
                else:
                    self.molecular_function = [gene_annotations["go"]["MF"]]
            else:
                self.molecular_function = None

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
            else:
                self.refseq_rna = None
        else:
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
            if isinstance(gene_annotations["genomic_pos"], list):
                self.chromosome = []
                self.startpos = []
                self.endpos = []
                for i in range(len(gene_annotations["genomic_pos"])):
                    if gene_annotations["genomic_pos"][i]["chr"] in ProteinBoxBotKnowledge.chromosomes[
                        self.genomeInfo["name"]].keys():
                        self.chromosome.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][
                                                   gene_annotations["genomic_pos"][i]["chr"]])
                        self.startpos.append(gene_annotations["genomic_pos"][i]["start"])
                        self.endpos.append(gene_annotations["genomic_pos"][i]["end"])
            else:
                self.chromosome = []
                self.startpos = []
                self.endpos = []
                if gene_annotations["genomic_pos"]["chr"] in ProteinBoxBotKnowledge.chromosomes[
                    self.genomeInfo["name"]].keys():
                    self.chromosome.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][
                                               gene_annotations["genomic_pos"]["chr"]])
                    self.startpos.append(gene_annotations["genomic_pos"]["start"])
                    self.endpos.append(gene_annotations["genomic_pos"]["end"])

        self.chromosomeHg19 = None
        self.startposHg19 = None
        self.endposHg19 = None
        if "genomic_pos_hg19" in gene_annotations:
            if isinstance(gene_annotations["genomic_pos_hg19"], list):
                self.chromosomeHg19 = []
                self.startposHg19 = []
                self.endposHg19 = []
                for i in range(len(gene_annotations["genomic_pos_hg19"])):
                    if gene_annotations["genomic_pos_hg19"][i]["chr"] in ProteinBoxBotKnowledge.chromosomes[
                        self.genomeInfo["name"]].keys():
                        self.chromosomeHg19.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][
                                                       gene_annotations["genomic_pos_hg19"][i]["chr"]])
                        self.startposHg19.append(gene_annotations["genomic_pos_hg19"][i]["start"])
                        self.endposHg19.append(gene_annotations["genomic_pos_hg19"][i]["end"])
            else:
                self.chromosomeHg19 = []
                self.startposHg19 = []
                self.endposHg19 = []
                if gene_annotations["genomic_pos_hg19"]["chr"] in ProteinBoxBotKnowledge.chromosomes[
                    self.genomeInfo["name"]].keys():
                    self.chromosomeHg19.append(ProteinBoxBotKnowledge.chromosomes[self.genomeInfo["name"]][
                                                   gene_annotations["genomic_pos_hg19"]["chr"]])
                    self.startposHg19.append(gene_annotations["genomic_pos_hg19"]["start"])
                    self.endposHg19.append(gene_annotations["genomic_pos_hg19"]["end"])

        # type of Gene
        if "type_of_gene" in gene_annotations:
            self.type_of_gene = []
            if gene_annotations["type_of_gene"] == "ncRNA":
                self.type_of_gene.append("Q427087")
            if gene_annotations["type_of_gene"] == "snRNA":
                self.type_of_gene.append("Q284578")
            if gene_annotations["type_of_gene"] == "snoRNA":
                self.type_of_gene.append("Q284416")
            if gene_annotations["type_of_gene"] == "rRNA":
                self.type_of_gene.append("Q215980")
            if gene_annotations["type_of_gene"] == "tRNA":
                self.type_of_gene.append("Q201448")
            if gene_annotations["type_of_gene"] == "pseudo":
                self.type_of_gene.append("Q277338")
            if gene_annotations["type_of_gene"] == "protein-coding":
                self.type_of_gene.append("Q20747295")
        else:
            self.type_of_gene = None
        # Reference section  
        # Prepare references
        refStatedIn = PBB_Core.WDItemID(value=self.genomeInfo["release"], prop_nr='P248', is_reference=True)
        refImported = PBB_Core.WDItemID(value='Q20641742', prop_nr='P143', is_reference=True)
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        gene_reference = [refStatedIn, refImported, refRetrieved]

        genomeBuildQualifier = PBB_Core.WDItemID(value=self.genomeInfo["genome_assembly"], prop_nr='P659',
                                                 is_qualifier=True)
        genomeBuildPreviousQualifier = PBB_Core.WDItemID(value=self.genomeInfo["genome_assembly_previous"],
                                                         prop_nr='P659', is_qualifier=True)

        prep = dict()
        prep['P703'] = [PBB_Core.WDItemID(value=self.genomeInfo['wdid'], prop_nr='P703',
                                          references=[copy.deepcopy(gene_reference)])]
        prep['P353'] = [
            PBB_Core.WDString(value=self.symbol, prop_nr='P353', references=[copy.deepcopy(gene_reference)])]
        prep['P351'] = [
            PBB_Core.WDString(value=str(self.entrezgene), prop_nr='P351', references=[copy.deepcopy(gene_reference)])]
        prep['P279'] = [PBB_Core.WDItemID(value='Q7187', prop_nr='P279', references=[copy.deepcopy(gene_reference)])]
        if "type_of_gene" in vars(self):
            if self.type_of_gene != None:
                for i in range(len(self.type_of_gene)):
                    prep['P279'].append(PBB_Core.WDItemID(value=self.type_of_gene[i], prop_nr='P279',
                                                          references=[copy.deepcopy(gene_reference)]))
        prep["P686"] = []
        if "molecular_function" in vars(self) and self.molecular_function:
            prep["P680"] = []
            for mf in self.molecular_function:
                term_reference = [copy.deepcopy(gene_reference)]
                if "pubmed" in mf.keys():
                    if isinstance(mf["pubmed"], list):
                        for pubmed in mf["pubmed"]:
                            term_reference.append(
                                PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(pubmed),
                                               prop_nr="P698", is_reference=True))
                    else:
                        term_reference.append(
                            PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(mf["pubmed"]),
                                           prop_nr="P698", is_reference=True))
                if mf["term"] in self.molecular_function_index.keys():
                    prep["P680"].append(
                        PBB_Core.WDItemID(value=self.molecular_function_index[mf["term"]], prop_nr='P680',
                                        references=term_reference))
                else:
                    raise Exception(str(self.entrezgene) + " "+mf["term"] + " is not covered in Wikidata yet")
                prep["P686"].append(
                       PBB_Core.WDString(value=mf["id"], prop_nr='P686', references=term_reference))

        if "cell_component" in vars(self):
            if self.cell_component != None:
                prep["P681"] = []
                for cc in self.cell_component:
                    term_reference = [copy.deepcopy(gene_reference)]
                    if "pubmed" in cc.keys():
                        if isinstance(cc["pubmed"], list):
                            for pubmed in cc["pubmed"]:
                                term_reference.append(
                                    PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(pubmed),
                                                   prop_nr="P698", is_reference=True))
                        else:
                            term_reference.append(
                                PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(cc["pubmed"]),
                                               prop_nr="P698", is_reference=True))
                    if cc["term"] in self.cell_componenent_index.keys():
                        prep["P681"].append(
                            PBB_Core.WDItemID(value=self.cell_componenent_index[cc["term"]], prop_nr='P681',
                                              references=term_reference))
                    else:
                        raise Exception(str(self.entrezgene) + " "+cc["term"] + " is not covered in Wikidata yet")
                    prep["P686"].append(
                       PBB_Core.WDString(value=cc["id"], prop_nr='P686', references=term_reference))

        if "biological_process" in vars(self) and self.biological_process is not None:
            prep["P682"] = []
            for bp in self.biological_process:
                term_reference = [copy.deepcopy(gene_reference)]
                if isinstance(bp, dict):
                    if "pubmed" in bp.keys():
                        if isinstance(bp["pubmed"], list):
                            for pubmed in bp["pubmed"]:
                                term_reference.append(
                                    PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(pubmed),
                                                   prop_nr="P698", is_reference=True))
                        else:
                            term_reference.append(
                                PBB_Core.WDUrl(value="http://www.ncbi.nlm.nih.gov/pubmed/" + str(bp["pubmed"]),
                                               prop_nr="P698", is_reference=True))

                    if bp["term"] in self.biological_process_index.keys():
                        prep["P682"].append(
                            PBB_Core.WDItemID(value=self.biological_process_index[bp["term"]], prop_nr='P682',
                                              references=term_reference))
                    else:
                        raise Exception(str(self.entrezgene) + " "+bp["term"] + " is not covered in Wikidata yet")
                    prep["P686"].append(
                       PBB_Core.WDString(value=bp["id"], prop_nr='P686', references=term_reference))

        if "ensembl_gene" in vars(self):
            if self.ensembl_gene != None:
                prep['P594'] = []
                for ensemblg in self.ensembl_gene:
                    prep['P594'].append(
                        PBB_Core.WDString(value=ensemblg, prop_nr='P594', references=[copy.deepcopy(gene_reference)]))

        if "ensembl_transcript" in vars(self):
            if self.ensembl_transcript != None:
                prep['P704'] = []
                for ensemblt in self.ensembl_transcript:
                    prep['P704'].append(
                        PBB_Core.WDString(value=ensemblt, prop_nr='P704', references=[copy.deepcopy(gene_reference)]))

        if "hgnc" in vars(self):
            if self.hgnc != None:
                prep['P354'] = []
                for hugo in self.hgnc:
                    prep['P354'].append(
                        PBB_Core.WDString(value=hugo, prop_nr='P354', references=[copy.deepcopy(gene_reference)]))

        if "homologene" in vars(self):
            if self.homologene != None:
                prep['P593'] = []
                for ortholog in self.homologene:
                    prep['P593'].append(
                        PBB_Core.WDString(value=ortholog, prop_nr='P593', references=[copy.deepcopy(gene_reference)]))

        if "refseq_rna" in vars(self):
            if self.refseq_rna != None:
                prep['P639'] = []
                for refseq in self.refseq_rna:
                    prep['P639'].append(
                        PBB_Core.WDString(value=refseq, prop_nr='P639', references=[copy.deepcopy(gene_reference)]))

        if "chromosome" in vars(self):
            prep['P1057'] = []
            if self.chromosome != None:
                for chrom in list(set(self.chromosome)):
                    prep['P1057'].append(
                        PBB_Core.WDItemID(value=chrom, prop_nr='P1057', references=[copy.deepcopy(gene_reference)]))

        if "startpos" in vars(self):
            if not 'P644' in prep.keys():
                prep['P644'] = []
            if self.startpos != None:
                for pos in self.startpos:
                    prep['P644'].append(
                        PBB_Core.WDString(value=str(pos), prop_nr='P644', references=[copy.deepcopy(gene_reference)],
                                          qualifiers=[copy.deepcopy(genomeBuildQualifier)]))
        if "endpos" in vars(self):
            if not 'P645' in prep.keys():
                prep['P645'] = []
            if self.endpos != None:
                for pos in self.endpos:
                    prep['P645'].append(
                        PBB_Core.WDString(value=str(pos), prop_nr='P645', references=[copy.deepcopy(gene_reference)],
                                          qualifiers=[copy.deepcopy(genomeBuildQualifier)]))

        if "startposHg19" in vars(self):
            if not 'P644' in prep.keys():
                prep['P644'] = []
            if self.startposHg19 != None:
                for pos in self.startposHg19:
                    prep['P644'].append(
                        PBB_Core.WDString(value=str(pos), prop_nr='P644', references=[copy.deepcopy(gene_reference)],
                                          qualifiers=[copy.deepcopy(genomeBuildPreviousQualifier)]))
        if "endposHg19" in vars(self):
            if not 'P644' in prep.keys():
                prep['P645'] = []
            if self.endposHg19 != None:
                for pos in self.endposHg19:
                    prep['P645'].append(
                        PBB_Core.WDString(value=str(pos), prop_nr='P645', references=[copy.deepcopy(gene_reference)],
                                          qualifiers=[copy.deepcopy(genomeBuildPreviousQualifier)]))

        if "MGI" in vars(self):
            prep['P671'] = []
            if self.MGI != None:
                for mgi in self.MGI:
                    prep['P671'].append(PBB_Core.WDString(value=mgi, prop_nr='P671'),
                                        references=[copy.deepcopy(gene_reference)])

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
            wdPage = PBB_Core.WDItemEngine(self.wdid, item_name=self.name, data=data2add, server="www.wikidata.org",
                                           domain="genes")
            wdPage.set_description(description=self.genomeInfo['name'] + ' gene', lang='en')
            if self.synonyms != None:
                wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
            print(self.wdid)
            self.wd_json_representation = wdPage.get_wd_json_representation()
            PBB_Debug.prettyPrint(self.wd_json_representation)
            PBB_Debug.prettyPrint(data2add)
            # print(self.wd_json_representation)
            # wdPage.write(self.logincreds)
        else:
            wdPage = PBB_Core.WDItemEngine(item_name=self.name, data=data2add, server="www.wikidata.org",
                                           domain="genes")
            wdPage.set_description(description=self.genomeInfo['name'] + ' gene', lang='en')
            if self.synonyms != None:
                wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
            self.wd_json_representation = wdPage.get_wd_json_representation()
            PBB_Debug.prettyPrint(self.wd_json_representation)
            PBB_Debug.prettyPrint(data2add)
            # print(self.wd_json_representation)
            # wdPage.write(self.logincreds)

    def annotate_gene(self):
        # "Get gene annotations from mygene.info"     
        r = requests.get(mygene_info_settings.getGeneAnnotationsURL() + str(self.entrezgene))
        return r.json()
        # return request.data
