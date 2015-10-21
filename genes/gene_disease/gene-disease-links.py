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

__author__ = 'Justin Leong, Andra Waagmeester'
__license__ = 'GPL'

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import requests
import copy
import pprint


# In this bot we will be extending gene items in Wikidata with gene disease links from .....
'''
First we need to obtain the Wikidata identifier (Qxxxxxx) for each Disease and Entrez Gene. Until now we have used the
WDQ (https://wdq.wmflabs.org/), With the public release of the SPARQL endpoint a second possibilities is to use SPARQL queries to get
these. For now I would continue with the WDQ.
'''


# Get Wikidata Ids for all entrez genes in Wikidata.
ncbi_gene_wikidata_ids = dict()
print("Getting all terms with a Disease Ontology ID in WikiData (WDQ)")
wdq_query = "CLAIM[703:{}] AND CLAIM[351]".format(self.genomeInfo["wdid"].replace("Q", ""))
ncbi_gene_in_wikidata = PBB_Core.WDItemList(wdqQuery, wdprop="351")
for geneItem in ncbi_gene_in_wikidata.wditems["props"]["351"]:
            ncbi_gene_wikidata_ids[str(geneItem[2])] = geneItem[0] # geneItem[2] = NCBI genecid identifier, geneItem[0] = WD identifier

#  Get all WikiData entries for Disease ontology terms in Wikidata through WDQ
print("Getting all terms with a Disease Ontology ID in WikiData (WDQ)")
do_wikidata_ids = dict()
do_in_wikidata = PBB_Core.WDItemList("CLAIM[699]", "699")
for diseaseItem in do_in_wikidata.wditems["props"]["699"]:
           do_wikidata_ids[str(diseaseItem[2])]=diseaseItem[0] # diseaseItem[2] = DO identifier, diseaseItem[0] = WD identifier


# Get from gene-disease links Phenocarta
source =  "http://www.chibi.ubc.ca/Gemma/phenocarta/LatestEvidenceExport/AnnotationsByDataset/OMIM.tsv"
result = requests.get(source, stream=True)
for line in result.iter_lines():
    # First separate each tuple into distinct fields.
    values = dict()
    s = str(line)
    fields = s.split("\\t")
    print(fields[0])
    values["Gene NCBI"] = fields[1]
    values["Gene Symbol"] = fields[2]
    values["Taxon"] = fields[3]
    values["Relationship"] = fields[4]
    values["Phenotype URIs"] = fields[5]
    values["Pubmeds"] = fields[6]
    values["gene_wdid"] = ncbi_gene_wikidata_ids[values["Gene NCBI"]]
    values["do_wdid"] = do_wikidata_ids[values["Phenotype URIs"]] # If multiple DO items exists in one row, we need to adapt this

    # Prepare references - Here we prepare the reference items to be added to each statement added by your bot
    # In other bots we also use stated in 'P248' for gnees, diseases or reference URL P854 for proteins. If you use P248
    # you need to make a Wikidata item for each version.

    refImported = PBB_Core.WDItemID(value='<WDItem id for Phenocarta', prop_nr='P143', is_reference=True)
    refImported.overwrite_references = True
    timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
    refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
    refRetrieved.overwrite_references = True
    phenocarta_reference = [refImported, refRetrieved]

    # Prepare the Wikidata statements
    prep = dict()
    # Statement pointing to a Wikidata item
    prep["Pxxxx"] = [PBB_Core.WDItemID(value='<Qxxxxxxx>', prop_nr='Pxxxx', references=[copy.deepcopy(phenocarta_reference)])]
    # Statement with a string as ?object
    prep["Pyyyy"] = [PBB_Core.WDString(value='<Qyyyyyyy>', prop_nr='Pyyyy', references=[copy.deepcopy(phenocarta_reference)])]

    # If you need to add multiple statements of the same property, you can use the following snippet
    id_list = ['23456', '53466', 'abcde']

    prep["Pzzzz"] = []
    for id in id_list:
        prep["Pzzzz"].append(PBB_Core.WDString(value="<string>", prop_nr='Pzzzz', references=[copy.deepcopy(phenocarta_reference)]))

    data2add = []
    for key in prep.keys():
        for statement in prep[key]:
            data2add.append(statement)

    # login to Wikidata
    login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

    # Get a pointer to the Wikidata page on the gene under scrutiny
    wd_gene_page = PBB_Core.WDItemEngine(values["gene_wdid"], data=data2add, server="www.wikidata.org", domain="genes")
    wd_json_representation = wd_gene_page.get_wd_json_representation()
    pprint.pprint(wd_json_representation)

    # Write to Wikidata
    wd_gene_page.write(login)







