__author__ = 'egonw' # 0000-0001-7542-0286

# set the following two env variables (e.g. with EXPORT):
#  wikidataUser -> user name
#  wikidataApi  -> password

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

def getMetabolitesFromWP():

    # Use the PubChem API to look up the SMILES, InChI, and InChIKey using the
    # PubChem CID provided by WikiPathways
    def get_inchi_key(cid):
        # use the RDF REST API
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/rdf/descriptor/{}_IUPAC_InChI.json".format(cid)
        print(url)
        inchiresults = requests.get(url)
        inchicall = inchiresults.json()
        smilescall = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/rdf/descriptor/{}_Isomeric_SMILES.json".format(cid)).json()
        inchikeycall = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/rdf/descriptor/{}_IUPAC_InChIKey.json".format(cid)).json()
        result = dict()
        result["inchi"]=inchicall["descriptor/{}_IUPAC_InChI".format(cid)]["http://semanticscience.org/resource/has-value"]["value"]
        result["smiles"]=smilescall["descriptor/{}_Isomeric_SMILES".format(cid)]["http://semanticscience.org/resource/has-value"]["value"]
        result["inchikey"]=inchikeycall["descriptor/{}_IUPAC_InChIKey.json".format(cid)]["http://semanticscience.org/resource/has-value"]["value"]
        return result

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
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr=u'P813', is_reference=True)
        refRetrieved.overwrite_references = True
        # P854 = reference URL
        refURL = PBB_Core.WDUrl(value=u"http://identifiers.org/wikipathways/" + str(wpurl), prop_nr=u'P854', is_reference=True)
        refURL.overwrite_references = True
        wp_reference = [refStatedIn, refRetrieved, refWpId, refURL]
        return wp_reference

    # source ref to PubChem
    def pc_reference(pcid):
        # P248 = Stated in: Q278487 = PubChem
        refStatedIn = PBB_Core.WDItemID(value="Q278487", prop_nr='P248', is_reference=True)
        refStatedIn.overwrite_references = True
        # P662 = PubChem ID (CID)
        refPcId = PBB_Core.WDString(value=str(pcid), prop_nr='P662', is_reference=True)
        refPcId.overwrite_references = True
        # P813 = retrieved
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        pc_reference = [refStatedIn, refPcId, refRetrieved]
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
        compound ["pubchem_reference"] = pc_reference(compound ["pubchem"])
        compounds.append(compound)

    return compounds

mappingSparql = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT DISTINCT ?mb ?pubchemCID ?wikidata
WHERE {

  SERVICE <https://query.wikidata.org/bigdata/namespace/wdq/sparql> {
    ?wd_item wdt:P662  ?wd_pubchem_cid .
  }

  ?mb a wp:Metabolite ;
  dc:source "PubChem-compound"^^xsd:string;
  dcterms:identifier ?pubchemCID ;
  wp:bdbWikidata ?wikidata .
  FILTER (str(?pubchemCID) = str(?wd_pubchem_cid))
}
    """

def getPubchemMappings():
        ## Pubchem mappings
        pbcreq = requests.get(
          "http://sparql.wikipathways.org/?default-graph-uri=&query=" +
          urllib.quote(mappingSparql) +
          "&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on"
        )
        pbres = pbcreq.json()
        pubchem_mappings = dict()
        for result in pbres["results"]["bindings"]:
            pubchem_mappings[str(result["pubchemCID"]["value"])] = result["wikidata"]["value"].replace('http://www.wikidata.org/entity/', '')
        pprint.pprint(pubchem_mappings)
        return pubchem_mappings

found_in_taxon_Qualifier = PBB_Core.WDItemID(value='Q15978631', prop_nr='P703', is_qualifier=True)
logincreds = PBB_login.WDLogin(os.environ['wikidataUser'], os.environ['wikidataApi'])

wp_metabolites = getMetabolitesFromWP()
pubchem_mappings = getPubchemMappings()
for metabolite in wp_metabolites:
    print(str(metabolite["pubchem"]))
    #if str(metabolite["pubchem"][0]).replace("http://identifiers.org/pubchem.compound/", "") in pubchem_mappings.keys():
    if str(metabolite["pubchem"][0]).replace("http://identifiers.org/pubchem.compound/", "") == "116545":
        prep = dict()
        # P31 = instance of P31, Q407595 = metabolite
        prep[u"P31"] = [
          PBB_Core.WDItemID(
            value='Q407595', prop_nr=u'P31',
            references=[copy.deepcopy(metabolite["wp_reference"])],
            qualifiers=[found_in_taxon_Qualifier]
          )
        ]
        # PubChem ID (CID) P662
        prep[u"P662"] = [
          PBB_Core.WDString(
            value=str(metabolite["pubchem"][0]).replace("http://identifiers.org/pubchem.compound/", ""),
            prop_nr=u'P662',
            references=[copy.deepcopy(metabolite["wp_reference"])]
          )
        ]
        # Canonical SMILES P233
        prep[u"P233"] = [
          PBB_Core.WDString(
            value=metabolite["smiles"], prop_nr=u'P233',
            references=[copy.deepcopy(metabolite["pubchem_reference"])]
          )
        ]
        # InChI P234
        prep[u"P234"] = [
          PBB_Core.WDString(
            value=metabolite["inchi"], prop_nr=u'P234',
            references=[copy.deepcopy(metabolite["pubchem_reference"])]
          )
        ]
        # InChIKey P235
        prep[u"P235"] = [
          PBB_Core.WDString(
            value=metabolite["inchikey"], prop_nr=u'P235',
            references=[copy.deepcopy(metabolite["pubchem_reference"])]
          )
        ]

        data2add = []
        for key in prep.keys():
            for statement in prep[key]:
                data2add.append(statement)
        wdPage = PBB_Core.WDItemEngine("Q26690136", data=data2add, server="www.wikidata.org",
                                               domain="drugs")
        output = wdPage.get_wd_json_representation()
        pprint.pprint(output)
        sys.exit()

