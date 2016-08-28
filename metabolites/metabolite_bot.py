__author__ = 'egonw' # 0000-0001-7542-0286

# set the following two env variables (e.g. with EXPORT):
#  wikidataUser -> user name
#  wikidataApi  -> password
#
# Needs Python 2.6/7 (does not work with Python 3)
#
# python metabolite_bot.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings
import pprint
try:
    import simplejson as json
except ImportError as e:
    import json

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from time import gmtime, strftime
import copy
import pprint
import urllib

# Use the PubChem API to look up the SMILES, InChI, and InChIKey using the
# PubChem CID provided by WikiPathways
def get_inchi_key(cid):
    # use the RDF REST API
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/property/InChI,InChIKey,CanonicalSMILES/JSON".format(str(cid))
    print(url)
    results = requests.get(url)
    pccall = results.json()
    result = dict()
    result["inchi"]    = pccall["PropertyTable"]["Properties"][0]["InChI"]
    result["inchikey"] = pccall["PropertyTable"]["Properties"][0]["InChIKey"]
    result["smiles"]   = pccall["PropertyTable"]["Properties"][0]["CanonicalSMILES"]
    return result

# inspired by ../compound/compound_protein_bot.pyt
def get_identifier_wikidata_map(property):
    sparql = """
        SELECT ?wikidata ?extid WHERE {{
            ?wikidata wdt:{} ?extid .
        }}
    """.format(property)

    queryParams = {'query': sparql, 'format': 'json'}
    httpHeaders = {'Accept': 'application/sparql-results+json'}
    url = 'https://query.wikidata.org/sparql'

    results = requests.get(url, params=queryParams, headers=httpHeaders).json()['results']['bindings']

    identifier_wikidata_map = dict()
    for mapping in results:
        identifier_wikidata_map[mapping['extid']['value']] = mapping['wikidata']['value'].split('/')[-1]

    return identifier_wikidata_map

def getMetabolitesFromWP():

    # source ref to WikiPathways
    def wp_reference(wpid, wpurl):
        # P248 = Stated in: Q7999828 = Wikipathways
        refStatedIn = PBB_Core.WDItemID(value="Q7999828", prop_nr=u'P248', is_reference=True)
        refStatedIn.overwrite_references = True
        # P2410 = WikiPathways ID
        refWpId = PBB_Core.WDString(value=u''+str(wpid[0]), prop_nr=u'P2410', is_reference=True)
        refWpId.overwrite_references = True
        # P813 = retrieved
        timeStringNow = u''+strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr=u'P813', is_reference=True, calendarmodel=u'http://www.wikidata.org/entity/Q1985727')
        refRetrieved.overwrite_references = True
        # P854 = reference URL
        refURL = PBB_Core.WDUrl(value=u"http://identifiers.org/wikipathways/" + str(wpurl), prop_nr=u'P854', is_reference=True)
        refURL.overwrite_references = True
        wp_reference = [refStatedIn, refRetrieved, refWpId, refURL]
        return wp_reference

    # source ref to PubChem
    def pc_reference(pcid):
        # P248 = Stated in: Q278487 = PubChem
        refStatedIn = PBB_Core.WDItemID(value="Q278487", prop_nr=u'P248', is_reference=True)
        refStatedIn.overwrite_references = True
        # P662 = PubChem ID (CID)
        refPcId = PBB_Core.WDExternalID(value=u''+str(pcid), prop_nr=u'P662', is_reference=True)
        refPcId.overwrite_references = True
        # P813 = retrieved
        timeStringNow = u''+strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr=u'P813', is_reference=True, calendarmodel=u'http://www.wikidata.org/entity/Q1985727')
        refRetrieved.overwrite_references = True
        # P854 = reference URL
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/property/InChI,InChIKey,CanonicalSMILES/JSON".format(str(pcid))
        refURL = PBB_Core.WDUrl(value=u'' + url, prop_nr=u'P854', is_reference=True)
        refURL.overwrite_references = True
        pc_reference = [refStatedIn, refPcId, refRetrieved, refURL]
        return pc_reference

    wpSparql = """
SELECT DISTINCT
  ?metabolite ?metabolite_label ?identifier ?identifierUri
  (GROUP_CONCAT(DISTINCT(?pathway); separator=", ") as ?pathways)
WHERE {
  ?metabolite a wp:Metabolite ;
    rdfs:label ?metabolite_label ;
    dcterms:identifier ?identifier ;
    dc:identifier ?identifierUri ;
    dc:source "PubChem-compound"^^xsd:string ;
    dcterms:isPartOf ?pathway .
  ?pathway a wp:Pathway ;
    dc:identifier ?wp_id ;
    wp:organismName "Homo sapiens"^^xsd:string .
}
    """

    x = requests.get(
      "http://sparql.wikipathways.org/?default-graph-uri=&query=" +
      urllib.quote(wpSparql) +
      "&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on"
    )
    res = x.json()
    compounds = []
    for result in res["results"]["bindings"]:
        compound = dict()

        if "metabolite_label" not in compound .keys():
            compound["metabolite_label"] = []
        compound["metabolite_label"].append(result["metabolite_label"]["value"])

        if "pubchem" not in compound.keys():
            compound["pubchem"] = []
        compound["pubchem"].append(result["metabolite"]["value"].replace("http://rdf.ncbi.nlm.nih.gov/pubchem.compound/",  ""))
        if "pubchemUri" not in compound.keys():
            compound["pubchemUri"] = []
        compound["pubchemUri"].append(result["identifierUri"]["value"])
        if "pathway" not in compound .keys():
            compound["pathway"] = []
        compound["pathway"].append(result["pathways"]["value"].replace("http://identifiers.org/wikipathways/",  ""))
        if "pw_id" not in compound .keys():
            compound["pw_id"] = []
        compound["pw_id"].append(result["pathways"]["value"].replace("http://identifiers.org/wikipathways/",  "").split("_")[0])
        if "revision" not in compound .keys():
            compound ["revision"] = []
        compound["revision"].append(result["pathways"]["value"].replace("http://identifiers.org/wikipathways/",  "").split("_")[1])

        compound ["wp_reference"] = wp_reference(compound ["pw_id"], compound["pathway"][0])
        pccid = str(compound["pubchem"][0]).replace("http://identifiers.org/pubchem.compound/", "")
        compound ["pubchem_reference"] = pc_reference(pccid)
        compounds.append(compound)

    return compounds

logincreds = PBB_login.WDLogin(os.environ['wikidataUser'], os.environ['wikidataApi'])

wp_metabolites = getMetabolitesFromWP()
pccid_mappings = get_identifier_wikidata_map("P662")
inchikey_mappings = get_identifier_wikidata_map("P235")
itemsEdited = 0
maxItems = 1
for metabolite in wp_metabolites:
    if itemsEdited >= maxItems:
      print("Done after editing #items: " + str(itemsEdited))
      sys.exit() # stop after one action, until the bot is approved, then 10, etc
    else:
      pccid = str(metabolite["pubchem"][0]).replace("http://identifiers.org/pubchem.compound/", "")
      print("considering: " + str(pccid))
      results = get_inchi_key(pccid)
      inWikidata = False
      qid = ""
      if pccid in pccid_mappings:
        qid = pccid_mappings[pccid]
        print("Found PubChem CID in Wikidata: " + qid);
        inWikidata = True
      elif (results["inchikey"]): # only proceed if we have an InChIKey from PubChem
        inchikey = results["inchikey"]
        print("Found an InChIKey on PubChem: " + inchikey)
        if inchikey in inchikey_mappings:
          qid = inchikey_mappings[inchikey]
          print("Found the InChIKey in Wikidata: " + qid);
          inWikidata = True

      if inWikidata:
        prep = dict()
        # P703 = found in taxon, Q15978631 = Homo sapiens
        prep[u"P703"] = [
          PBB_Core.WDItemID(
            value='Q15978631', prop_nr=u'P703', rank=u'normal',
            references=[copy.deepcopy(metabolite["wp_reference"])]
          )
        ]

        if (results["inchikey"]): # only proceed if we have an InChIKey from PubChem
          inchikey = results["inchikey"]
          print("Found an InChIKey on PubChem: " + inchikey)
          if inchikey in inchikey_mappings:
            print("Found the InChIKey in Wikidata: " + inchikey_mappings[inchikey]);

          # now do the workload
          data2add = []
          for key in prep.keys():
            for statement in prep[key]:
                data2add.append(statement)
          wdPage = PBB_Core.WDItemEngine(
            qid, server="www.wikidata.org",
            data=data2add,
            domain="drugs", append_value=['P31','P233','P234','P235']
          )
          output = wdPage.get_wd_json_representation()
          pprint.pprint(output)
          #wdPage.write(logincreds)
          itemsEdited = itemsEdited + 1
      else:
        print("No Wikidata entry found for PubChem CID " + pccid + " (but creating one)")
        prep = dict()
        # P31 = instance of P31, Q407595 = metabolite, Q11173 = chemical compound
        prep[u"P31"] = [
          PBB_Core.WDItemID(
            value='Q11173', prop_nr=u'P31', rank=u'normal',
            references=[copy.deepcopy(metabolite["wp_reference"])]
          )
        ]
        # P703 = found in taxon, Q15978631 = Homo sapiens
        prep[u"P703"] = [
          PBB_Core.WDItemID(
            value='Q15978631', prop_nr=u'P703', rank=u'normal',
            references=[copy.deepcopy(metabolite["wp_reference"])]
          )
        ]
        # PubChem ID (CID) P662
        prep[u"P662"] = [
          PBB_Core.WDExternalID(
            value=u''+pccid,
            prop_nr=u'P662',
            references=[copy.deepcopy(metabolite["wp_reference"])]
          )
        ]
        # get some more details from PubChem
        # output Canonical SMILES P233
        if results["smiles"]:
          prep[u"P233"] = [
            PBB_Core.WDString(
              value=results["smiles"], prop_nr=u'P233',
              references=[copy.deepcopy(metabolite["pubchem_reference"])]
            )
          ]
        # InChI P234
        if results["inchi"]:
          prep[u"P234"] = [
            PBB_Core.WDString(
              value=results["inchi"].replace("InChI=",""), prop_nr=u'P234',
              references=[copy.deepcopy(metabolite["pubchem_reference"])]
            )
          ]
        # InChIKey P235
        if results["inchikey"]:
          prep[u"P235"] = [
            PBB_Core.WDString(
              value=results["inchikey"], prop_nr=u'P235',
              references=[copy.deepcopy(metabolite["pubchem_reference"])]
            )
          ]

        # now do the workload
        data2add = []
        for key in prep.keys():
          for statement in prep[key]:
              data2add.append(statement)
        wdPage = PBB_Core.WDItemEngine(
          item_name=metabolite["metabolite_label"][0], server="www.wikidata.org",
          data=data2add,
          domain="drugs"
        )
        wdPage.set_label(metabolite["metabolite_label"][0])
        wdPage.set_description("chemical compound found in a biologcal pathway")
        output = wdPage.get_wd_json_representation()
        #pprint.pprint(output)
        #wdPage.write(logincreds)
        #itemsEdited = itemsEdited + 1
