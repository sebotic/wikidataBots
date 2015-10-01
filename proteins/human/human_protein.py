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
import urllib
import requests
import copy
import traceback
import sys
import mygene_info_settings
from time import gmtime, strftime

try:
    import simplejson as json
except ImportError as e:
    import json
	
class human_proteome():
    def __init__(self):
        #self.content = self.download_human_proteins()
        #self.protein_count = len(self.content["results"]["bindings"])
        #self.proteins = self.content["results"]["bindings"]
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        uniprotWikidataIds = dict()
        GeneSymbolWdMapping = dict()
        print('Getting all proteins with a uniprot ID in Wikidata')
        InWikiData = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[352]", "352")
        print("Getting all human gene symbols in Wikidata")
        GeneSymbolMapping = PBB_Core.WDItemList("CLAIM[279:7187] AND CLAIM[353] AND CLAIM[703:5]", "353")
        for geneSymbol in GeneSymbolMapping.wditems["props"]["353"]:
            GeneSymbolWdMapping[str(geneSymbol[2]).lower()] = geneSymbol[0]
        for proteinItem in InWikiData.wditems["props"]["352"]:
            uniprotWikidataIds[str(proteinItem[2])] = proteinItem[0]
        for uniprotWDQId in uniprotWikidataIds.keys():
          try:
            """
            r = requests.get("http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f"+
                              str(uniprotWDQId)+
                              "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a++++++++%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09%09%3fgene+skos%3aprefLabel+%3fencodedBy+.%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b+%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%7b%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a++++++++%7b%3fupAlias+up%3ashortName+%3falias+.%7d%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fencodedBy+%3fplabel+%3fecName+%3fupversion&format=srj")
            """
            r = requests.get("http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%3fgwiki%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f"+
                              str(uniprotWDQId)+
                             "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a++++++++%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09%09%3fgene+skos%3aprefLabel+%3fencodedBy+.%0d%0a++++++++%3funiprot+rdfs%3aseeAlso+%3fgwiki+.%0d%0a++++++++%3fgwiki+up%3adatabase+database%3aGeneWiki+.%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias1+.%0d%0a++++++++%3fupAlias1+up%3aecName+%3fecName+.%7d%0d%0a++++++++%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a+++++++%7b%3funiprot+up%3aalternativeName+%3fupAlias+.+%0d%0a++++++++++%3fupAlias+up%3ashortName+%3falias+.%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3funiprot+%3fgwiki+%3fencodedBy+%3fplabel+%3fecName+%3fupversion&format=srj")


            # print r.text
            protein = json.loads(r.text)
            protein["logincreds"] = self.logincreds
            protein["wdid"] = 'Q'+str(uniprotWikidataIds[uniprotWDQId])
            # print protein
            protein["geneSymbols"] = GeneSymbolWdMapping
            proteinClass = human_protein(protein)
       
          except:
            f = open('/tmp/protein_exceptions.txt', 'a')
            # f.write("Unexpected error:", sys.exc_info()[0]+'\n')
            f.write(str(protein["results"]["bindings"][0]["uniprot"]["value"])+"\n")
            traceback.print_exc(file=f)
            f.ploep()
            f.close()
          
    def download_human_proteins(self):
        """
        Downloads the latest list of human proteins from uniprot through the URL specified in mygene_info_settings
        """
        print("Getting content from Uniprot")
        r = requests.get(mygene_info_settings.getUniprotUrl())
        return r.json(mygene_info_settings.getGeneWikiLinks())

    def download_genewiki_mappings(self):
        print("Getting GeneWiki Mappings from Uniprot")
        gwMappings = dict()
        content = requests.get(mygene_info_settings.getGeneWikiLinks())

        r = requests.get()

        
class human_protein(object):
    def __init__(self, object):
        # Populate variables with different values
        self.geneSymbols = object["geneSymbols"]
        print(object["geneSymbols"])
        self.logincreds = object["logincreds"]
        self.version = object["results"]["bindings"][0]["upversion"]["value"]
        self.wdid = object["wdid"]
        self.uniprot = object["results"]["bindings"][0]["uniprot"]["value"]
        self.uniprotId = object["results"]["bindings"][0]["uniprot"]["value"].replace("http://purl.uniprot.org/uniprot/", "").replace(" ", "")
        self.genewiki =  object["results"]["bindings"][0]["gwiki"]["value"].replace("http://purl.uniprot.org/genewiki/", "").replace(" ", "").replace("_", " ")
        self.name = object["results"]["bindings"][0]["plabel"]["value"]
        if "ecName" in object["results"]["bindings"][0].keys():
            self.ecname = object["results"]["bindings"][0]["ecName"]["value"]
        self.alias = []
        for syn in object["results"]["bindings"][0]["upalias"]["value"].split(";"):
            self.alias.append(syn)
        if "pdbid" in object["results"]["bindings"][0].keys() and object["results"]["bindings"][0]["pdbid"][
            "value"] != "":
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
            self.encoded_by.append('Q'+str(self.geneSymbols[str(encodedBy).lower()]))


        # Prepare references
        refURL = "http://www.uniprot.org/uniprot/"+self.uniprotId+".txt?"+str(self.version)
        #refStatedIn = PBB_Core.WDItemID(value=refURL, prop_nr='P248', is_reference=True)
        refReferenceURL = PBB_Core.WDUrl(value=refURL, prop_nr='P854', is_reference=True)
        refImported = PBB_Core.WDItemID(value='Q905695', prop_nr='P143', is_reference=True)
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        protein_reference =  [[refImported, refRetrieved, refReferenceURL]]

        references = dict()
        proteinPrep = dict()
        genePrep = dict()

        # P279 = subclass of
        proteinPrep['P279'] = [PBB_Core.WDItemID(value="Q8054", prop_nr='P279', references=protein_reference)]

        # P703 = found in taxon
        proteinPrep['P703'] = [PBB_Core.WDItemID(value="Q5", prop_nr='P703', references=protein_reference)]

        # P352 = UniprotID
        proteinPrep['P352'] = [PBB_Core.WDString(value=self.uniprotId, prop_nr='P352', references=protein_reference)]

        # P591 = EC number
        if "ecname" in vars(self):
            for i in range(len(self.ecname)):
                proteinPrep['P591'] = [PBB_Core.WDString(value=self.ecname[i], prop_nr='P591', references=protein_reference)]

        # P638 = PDBID
        if "pdb" in vars(self) and len(self.pdb) > 0:
            for i in range(len(self.pdb)):
                proteinPrep['P638'] = [PBB_Core.WDString(value=self.pdb[i], prop_nr='P638', references=protein_reference)]
                proteinPrep['P18'] = [PBB_Core.WDUrl(value="http://www.rcsb.org/pdb/images/{}_bio_r_500.jpg".format(self.pdb[i]), prop_nr='P18', references=protein_reference)]

        # P637 = Refseq Protein ID
        if "refseq" in vars(self) and len(self.refseq) > 0:
            for i in range(len(self.refseq)):
                proteinPrep['P637'] = [PBB_Core.WDString(value=self.refseq[i], prop_nr='P637', references=protein_reference)]

        # P705 = Ensembl Protein ID
        if "ensemblp" in vars(self) and len(self.ensemblp) > 0:
            for i in range(len(self.ensemblp)):
                proteinPrep['P705'] = [PBB_Core.WDString(value=self.ensemblp[i], prop_nr='P705', references=protein_reference)]

        # P702 = Encoded by
        if "encoded_by" in vars(self) and len(self.encoded_by) > 0:
            for i in range(len(self.encoded_by)):
                proteinPrep['P702'] = [PBB_Core.WDItemID(value=self.encoded_by[i], prop_nr='P702', references=protein_reference)]
                if self.encoded_by[i] in genePrep.keys():
                    genePrep[self.encoded_by[i]].append(PBB_Core.WDItemID(value=self.wdid, prop_nr='P688', references=protein_reference))
                else:
                    genePrep[self.encoded_by[i]] = [PBB_Core.WDItemID(value=self.wdid, prop_nr='P688', references=protein_reference)]

        proteinData2Add = []
        for key in proteinPrep.keys():
            for statement in proteinPrep[key]:
                proteinData2Add.append(statement)
                print(statement.prop_nr, statement.value)


        wdProteinpage = PBB_Core.WDItemEngine(wd_item_id=self.wdid, item_name=self.name, data=proteinData2Add, server="www.wikidata.org", references=references, domain="proteins")
        wdProteinpage.set_aliases(aliases=self.alias, lang='en', append=True)
        wdProteinpage.set_description(description='human protein', lang='en')
        self.wd_json_representation = wdProteinpage.get_wd_json_representation()


        PBB_Debug.prettyPrint(self.wd_json_representation)

        '''
        Adding the encodes property to gene pages
        '''
        for key in genePrep.keys():
            url = 'https://{}/w/api.php'.format("www.wikidata.org")
            params = {
                'action': 'wbgetentities',
                'sites': 'enwiki',
                'ids': key,
                'format': 'json'
            }

            reply = requests.get(url, params=params)

            wdLabel = reply.json()['entities'][key]['labels']['en']['value']

        wdGenePage = PBB_Core.WDItemEngine(wd_item_id=key, item_name = wdLabel, data=genePrep[key], server="www.wikidata.org", references=references, domain="genes")

        if self.genewiki == wdProteinpage.get_wd_sitelinks(site="enwiki")["title"]:
            PBB_Debug.prettyPrint(wdProteinpage.get_wd_sitelinks(site="enwiki"))
            wdGenePage.set_sitelink(site="enwiki", value = wdProteinpage.remove_sitelink(site="enwiki"))
            PBB_Debug.prettyPrint(wdGenePage.get_wd_json_representation())
            print(self.wdid)
            PBB_Debug.prettyPrint(wdProteinpage.get_wd_json_representation())

        wdProteinpage.write(self.logincreds)
        wdGenePage.write(self.logincreds)
        sys.exit()