#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author:Andra Waagmeester (andra@waagmeester.net)

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

# Import the required libraries
import urllib2
import simplejson
import json
# -*- coding: utf-8  -*-
import pywikibot
import pprint
from pywikibot.data import api
import sys
import ProteinBoxBotFunctions
import time

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

#references 
## databases
reference2entrezGene = pywikibot.ItemPage(repo, u'Q1345229')  
reference2ensembl = pywikibot.ItemPage(repo, u'Q1344256')

## species 
humanSpeciesPage = pywikibot.ItemPage(repo, u'Q5')
mouseSpeciesPage = pywikibot.ItemPage(repo, u'')
genePage = pywikibot.ItemPage(repo, u'Q7187')

if len(sys.argv) != 2:
    print "Usage: python ProteinBoxBotFunctions.addIdentifierMappingsProteinBoxBot.py <fileNameWithIds>"
    print " "
    print "For details see <>" #FIXME point to details documentation page when finished
else:
    # Initiate log files
    successLog = open(sys.argv[1]+'_succesfullyAdded.log', 'w')
    multipleEntriesLog = open(sys.argv[1]+'_multipleItems.log', 'w')
    multipleMyGeneEntriesLog = open(sys.argv[1]+'_multipleMyGeneEntries.log', 'w')
    noLabelLog = open(sys.argv[1]+'_noLabelsEntrezGene.log', 'w')
    typeErrorLog = open(sys.argv[1]+'_typeErrorsEntrezGene.log', 'w')
    multiplesubClassLog = open(sys.argv[1]+'_multipleSubclasses.log', 'w')
    timeLog = open(sys.argv[1]+'_performance.log', 'w')
    miscelaniousLog = open(sys.argv[1]+'_misc.log', 'w')
    iteration = 0
    with open(sys.argv[1], 'r') as myWikiDataItems:
      reference2resource = pywikibot.ItemPage(repo, 'Q1345229') # Entrez
      wdItems = myWikiDataItems.readlines()
      for wdItem in wdItems:
        while True:
            try:  
              ts = time.time()
              wdItem = wdItem.strip()
              itemFields = wdItem.split('\t')
              entrezID = itemFields[0]
              wikidataID = itemFields[1]
              print wikidataID
              item = pywikibot.ItemPage(repo, wikidataID)
              timeLog.write(entrezID+'\t'+str(ts)+'\n')
          
              # Get  details from MygeneInfo
              req=urllib2.Request("http://mygene.info/v2/gene/"+entrezID, None, {'user-agent':'ProteinBoxBot'})
              print "http://mygene.info/v2/gene/"+entrezID
              opener = urllib2.build_opener()
              f = opener.open(req)
              mygeneinfo = simplejson.load(f)
          
              if isinstance(mygeneinfo, list):
                  multipleMyGeneEntriesLog.write(entrezGeneId+": "+"http://mygene.info/v2/gene/"+entrezID+": Multiple entries in mygene.info"+"\n")
                  continue
              # Add Ensembl Id's
              if "ensembl" in mygeneinfo: 
                  ensemblEntries =  mygeneinfo["ensembl"]  # P594 = Entrez Gene Id
                  if isinstance(ensemblEntries, list):
                     multipleMyGeneEntriesLog.write(entrezID+": "+"http://mygene.info/v2/gene/"+entrezID+": Multiple Ensembl entries in mygene.info"+"\n")
                  else:
                     # Ensembl Gene
                     ProteinBoxBotFunctions.addIdentifier(site, repo, item, ensemblEntries["gene"], 'P594', reference2entrezGene) # P594 = Ensembl Gene Id
                     # Ensembl Transcript
                     ProteinBoxBotFunctions.addIdentifier(site, repo, item, ensemblEntries["transcript"], 'P704', reference2entrezGene) # P704 = Ensembl Transcript Id

              if "symbol" in mygeneinfo: ProteinBoxBotFunctions.addIdentifier(site, repo, item, mygeneinfo["symbol"], 'P353', reference2entrezGene) # P353 = gene symbol
              if "HGNC" in mygeneinfo: ProteinBoxBotFunctions.addIdentifier(site, repo, item, mygeneinfo["HGNC"], 'P354', reference2entrezGene) # P354 = HGNC ID
              if "homologene" in mygeneinfo: ProteinBoxBotFunctions.addIdentifier(site, repo, item, str(mygeneinfo["homologene"]["id"]), 'P593', reference2entrezGene) # P593 = homologene id

              if "refseq" in mygeneinfo: refseqEntries =  mygeneinfo["refseq"]
              if "rna" in refseqEntries: ProteinBoxBotFunctions.addIdentifier(site, repo, item, refseqEntries["rna"], 'P639', reference2entrezGene) # P639 = RefSeq RNA ID    
              #Add chromosome
              if "genomic_pos" in mygeneinfo: 
                  chromosomes = ProteinBoxBotFunctions.chromosomes
                  if (isinstance(mygeneinfo["genomic_pos"], list)):
                     chromosome = mygeneinfo["genomic_pos"][0]["chr"]
                  else: chromosome = mygeneinfo["genomic_pos"]["chr"]
                  if str(chromosome) in chromosomes:
                     chromosomepage = pywikibot.ItemPage(repo, chromosomes[str(chromosome)])
                     ProteinBoxBotFunctions. addStatement(site, repo, item, 'P1057', chromosomepage, reference2entrezGene)
                  else:
                     miscelaniousLog.write(entrezID+'\t'+"chromosomes at http://mygene.info/v2/gene/"+entrezID+"\tMessage: Chromosome is unknown")
              successLog.write(entrezID+'\t'+wikidataID+'\n')
            except:
                if iteration == 0: 
                    iteration = 1
                    time.sleep(5) # wait 5 seconds before retrying 
                elif iteration == 1:
                    iteration = 2 
                    time.sleep(60) # wait a minute before retrying
                elif iteration == 2:
                    iteration = 0
                    print "There has been an issue for over an hour"
                    time.sleep(3600) # wait an hour before retring             
                continue
            break
          