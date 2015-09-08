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

def getmyGeneInfoUrl():
    return 'http://mygene.info/v2/gene/'
    
def getHumanGenesUrl():
    return "http://mygene.info/v2/query?q=__all__&species=human&entrezonly=true&size=100000"
    
def getGeneAnnotationsURL():
    return "http://mygene.info/v2/gene/"
    
def getUniprotUrl():
    return "http://sparql.uniprot.org/sparql?query=PREFIX+wd%3a+%3chttp%3a%2f%2fwww.wikidata.org%2fentity%2f%3e%0d%0aPREFIX+wdt%3a+%3chttp%3a%2f%2fwww.wikidata.org%2fprop%2fdirect%2f%3e%0d%0aPREFIX+rdfs%3a+%3chttp%3a%2f%2fwww.w3.org%2f2000%2f01%2frdf-schema%23%3e%0d%0aPREFIX+p%3a+%3chttp%3a%2f%2fwww.wikidata.org%2fprop%2f%3e%0d%0aPREFIX+v%3a+%3chttp%3a%2f%2fwww.wikidata.org%2fprop%2fstatement%2f%3e%0d%0aPREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e+%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0a%0d%0aSELECT+DISTINCT+%3fwd_url+%3funiprot+%3fupversion+%3fproteinLabel+%0d%0a+++(group_concat(distinct+%3fupalias+%3bseparator%3d%22%3b+%22)+as+%3falias)%0d%0a+++(group_concat(distinct+%3fpfam+%3bseparator%3d%22%3b+%22)+as+%3fpfam_id)+%0d%0a+++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbId)%0d%0a+++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3fRefSeq_Id)%0d%0a+++(group_concat(distinct+%3fgoid%3b+separator%3d%22%3b+%22)+as+%3fupGoid)%0d%0aWHERE+%7b%0d%0aSERVICE+%3chttp%3a%2f%2fwdqs-beta.wmflabs.org%2fbigdata%2fnamespace%2fwdq%2fsparql%3e%7b%0d%0a+++%3fwd_url+wdt%3aP279+wd%3aQ8054+.%0d%0a+++%3fwd_url+rdfs%3alabel+%3fproteinLabel+.%0d%0a+++%3fwd_url+wdt%3aP352+%3fwduniprot+.%0d%0a+++FILTER(lang(%3fproteinLabel)+%3d+%22en%22)%0d%0a%7d%0d%0aBIND(IRI(CONCAT(%22http%3a%2f%2fpurl.uniprot.org%2funiprot%2f%22%2c+%3fwduniprot))+as+%3funiprot)+%0d%0a%0d%0a%0d%0a%3funiprot+rdfs%3aseeAlso+%3fpfam+.%0d%0a%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a%3funiprot+up%3aversion+%3fupversion+.++%0d%0a%3fpfam+up%3adatabase+database%3aPfam+.%0d%0a%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a%3fpdb+up%3adatabase+database%3aPDB+.%0d%0a%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a%3frefseq+up%3adatabase+database%3aRefSeq+.%0d%0a%3funiprot+up%3aclassifiedWith+%3fkeyword++.%0d%0a%3fkeyword+rdfs%3aseeAlso+%3fgoid++.%0d%0a%3fgoid+rdfs%3alabel+%3fgolabel++.%0d%0a%7d%0d%0aGROUP+BY+%3funiprot+%3fproteinLabel+%3fwd_url+%3fupversion&format=srj"