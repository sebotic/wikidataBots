'''
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

It is specifically built to remove erroneous entries made previously. In the first 2000
additions to WikiData a new addidtion was checked against existing entries in WikiData with the same label, without cheching if was 
already annotated as another subclass. This cause various WikiData entries to be annotated as being bot a subclass of Protein
and Gene. 
This bot rolls removes the statemens that were added erroneuous. 
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

def getClaims(site, wdItem, claimProperty):
    params = {
    			'action' :'wbgetclaims' ,
                'entity' : wdItem.getID(),
    			'property': claimProperty,
             }
    request = api.Request(site=site,**params)
    return request.submit()
    
def deleteClaims(site, wdPage, property, token):
    claims = getClaims(site, wdPage, property)
    if len(claims['claims']) > 0:
        for claim in claims['claims'][property]:
            pp.pprint(claim['id'])
            params = {'action':'wbremoveclaims', 'claim':claim['id'], 'bot':True, 'token':token}
            request = api.Request(site=site,**params)
            data = request.submit()

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()


pp = pprint.PrettyPrinter(indent=4)

with open('proteins.txt', 'r') as myWikiDataItems:
    wdItems = myWikiDataItems.readlines()
    for wdItem in wdItems:
        wdItem = wdItem.strip()
        print wdItem
        wdPage = pywikibot.ItemPage(repo, wdItem)

        token = repo.token(wdPage, 'edit')

        claims = getClaims(site, wdPage, 'P279')
        for claim in claims['claims']['P279']:
            if claim['mainsnak']['datavalue']['value']['numeric-id']==7187:
                params = {'action':'wbremoveclaims', 'claim':claim['id'], 'bot':True, 'token':token}
                request = api.Request(site=site,**params)
                data = request.submit()
    

        deleteClaims(site, wdPage, 'P351', token) # Entrez Gene ID
        deleteClaims(site, wdPage, 'P594', token) # Ensembl Gene 
        deleteClaims(site, wdPage, 'P704', token)
        deleteClaims(site, wdPage, 'P639', token) 
        deleteClaims(site, wdPage, 'P353', token) # gene symbol
        deleteClaims(site, wdPage, 'P354', token) # HGNC
        deleteClaims(site, wdPage, 'P593', token) # Homologene
        deleteClaims(site, wdPage, 'P1057', token) # chromosome
        



