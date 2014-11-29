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
import ProteinBoxBotKnowledge
        
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

from raven import Client

client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')

# record a simple message
client.captureMessage('ProteinBoxBot restarted manually')

if len(sys.argv) != 2:
    print "Usage: python ProteinBoxBoxTemplate.py <fileNameWithIds>"
    print " "
    print "For details see <>" #FIXME point to details documentation page when finished
else:
  # Initiate log files
  successLog = open(sys.argv[1]+'_succesfullyAdded.log', 'w')
  multipleEntriesLog = open(sys.argv[1]+'_multipleItems.log', 'w')
  multipleMyGeneEntriesLog = open(sys.argv[1]+'_multipleMyGeneEntries.log', 'w')
  noLabelLog = open(sys.argv[1]+'_noLabelsEntrezGene.log', 'w')
  typeErrorLog = open(sys.argv[1]+'_typeErrorsEntrezGene.log', 'w')
  multiplesubClassLog = open('/tmp/'+sys.argv[1]+'_multipleSubclasses.log', 'w')

  # A file with both an identifier and a label is required
  # The file should contain (separated by '\t')
  # 1. Globally unique identifier (required) Entry gene id
  # 2. Symbol
  # 3. Synonym
  # 4. Label 
  
  pp = pprint.PrettyPrinter(indent=4)
  with open(sys.argv[1], 'r') as myWikiDataItems:
    wdItems = myWikiDataItems.readlines()
    for wdItem in wdItems:
      # while True:
        try:  
          wdItem = wdItem.strip()
          itemFields = wdItem.split('\t')
          itemID = itemFields[0]
          localalias = itemFields[1]
          localotheralias = itemFields[2]
          localLabel = itemFields[3].replace("<", "&lt;").replace(">", "&gt;")
          if localLabel == "-": 
              continue
          # First count the number of occurences in WikiData for the given label
          
          print localLabel
          token = repo.token(pywikibot.Page(repo, localLabel), 'edit')
          print token
          # localdata = ProteinBoxBotFunctions.createNewPage(site, token)
          # ID = localdata['entity']['id']
          # print ID
          localdata={   u'entity': {   },
              u'success': 1}
          
          # Add Label
          localdata = ProteinBoxBotFunctions.addLabel(localdata, localLabel)
          # Add aliases
          localdata = ProteinBoxBotFunctions.addAliases(localdata, localalias, localotheralias)
          
          # Add claims
          localdata["entity"]["claims"] = dict()
          localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P279', [7187], 'wikibase-entityid') # subclass of (P279) Gene  
          localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P351', [itemID], 'string') # entrez ID Gene (P279)
          localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P703', [83310], 'wikibase-entityid') # found in taxon (P703) House mouse 83310
          
          req=urllib2.Request("http://mygene.info/v2/gene/"+itemID, None, {'user-agent':'ProteinBoxBot'})
          print "http://mygene.info/v2/gene/"+itemID
          opener = urllib2.build_opener()
          f = opener.open(req)
          mygeneinfo = simplejson.load(f)
          if isinstance(mygeneinfo, list):
              multipleMyGeneEntriesLog.write(itemID+": "+"http://mygene.info/v2/gene/"+itemID+": Multiple entries in mygene.info"+"\n")
              continue
          if "ensembl" in mygeneinfo: 
                ensemblEntries =  mygeneinfo["ensembl"]  # P594 = Entrez Gene Id
                if isinstance(ensemblEntries, list):
                    multipleMyGeneEntriesLog.write(itemID+": "+"http://mygene.info/v2/gene/"+itemID+": Multiple Ensembl entries in mygene.info"+"\n")
                else:
                    # Ensembl Gene
                    localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P594', ensemblEntries["gene"], 'string') # s# P594 = 
                    # Ensembl Transcript
                    localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P704', ensemblEntries["transcript"], 'string')

          if "symbol" in mygeneinfo: 
                localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P353', mygeneinfo["symbol"], 'string') #P353 = Symbol
          if "HGNC" in mygeneinfo: 
                localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P354', mygeneinfo["HGNC"], 'string') # P354 = HGNC ID
          if "homologene" in mygeneinfo: 
                localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P593', str(mygeneinfo["homologene"]["id"]), 'string')  # P593 = homologene id
          if "refseq" in mygeneinfo: 
                refseqEntries =  mygeneinfo["refseq"]
                if "rna" in refseqEntries: 
                    localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P639', refseqEntries["rna"], 'string') # P639 = RefSeq RNA ID    
                    #Add chromosome
          if "genomic_pos" in mygeneinfo: 
                if (isinstance(mygeneinfo["genomic_pos"], list)):
                    chromosome = mygeneinfo["genomic_pos"][0]["chr"]
                else: chromosome = mygeneinfo["genomic_pos"]["chr"]
                chromosomepage = pywikibot.ItemPage(repo, ProteinBoxBotKnowledge.mouseChromosomes[str(chromosome)])
                print str(chromosome)
                print ProteinBoxBotKnowledge.mouseChromosomes[str(chromosome)]
                print chromosomepage.getID()[1:]
                test = chromosomepage.getID()
                print test[1:]
                localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P1057', [chromosomepage.getID()[1:]], 'wikibase-entityid')
          localdata.pop("success", None)
          request = api.Request(site=site,
                                action='wbeditentity',
                                format='json',
                                new='item',
                                bot=True,
                                token=token,
                                data=json.dumps(localdata['entity']))
          # pp.pprint(localdata)
          data = request.submit()
          # pp.pprint(data)
          ID = data['entity']['id']
          print ID
          successLog.write(itemID+'\t'+ID+'\n') 
        except:
            client.captureException()
            # continue
        #break               
   
