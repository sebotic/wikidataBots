__author__ = 'egonw' # 0000-0001-7542-0286

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

def getMetabolitesFromWP():

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

    # ref to WikiPathways
    def wp_reference(wpid):
        # P248 = Stated in: Q7999828 = Wikipathways
        refStatedIn = PBB_Core.WDItemID(value="Q7999828", prop_nr='P248', is_reference=True)
        refStatedIn.overwrite_references = True
        refWpId = PBB_Core.WDString(value=str(wpid), prop_nr='P2410', is_reference=True)
        refWpId.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        wp_reference = [refStatedIn, refWpId, refRetrieved]
        return wp_reference

    # ref to PubChem
    def pc_reference(pcid):
        # P248 = Stated in: Q278487 = PubChem
        refStatedIn = PBB_Core.WDItemID(value="Q278487", prop_nr='P248', is_reference=True)
        refStatedIn.overwrite_references = True
        refPcId = PBB_Core.WDString(value=str(pcid), prop_nr='P2410', is_reference=True)
        refPcId.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        pc_reference = [refStatedIn, refPcId, refRetrieved]
        return pc_reference


    x = requests.get("http://sparql.wikipathways.org/?default-graph-uri=&query=SELECT+DISTINCT+%3Fmetabolite+%3Fmetabolite_label+%3Fidentifier+%3FidentifierUri+%28GROUP_CONCAT%28DISTINCT%28%3Fpathway%29%3B+separator%3D%22%2C+%22%29+as+%3Fpathways%29+WHERE+%7B%0D%0A%3Fmetabolite+a+wp%3AMetabolite+%3B%0D%0Ardfs%3Alabel+%3Fmetabolite_label+%3B%0D%0Adcterms%3Aidentifier+%3Fidentifier+%3B%0D%0A%09++++++dc%3Aidentifier+%3FidentifierUri+%3B%0D%0A%09++++++dc%3Asource+%22PubChem-compound%22%5E%5Exsd%3Astring+.%0D%0A%3Fmetabolite+dcterms%3AisPartOf+%3Fpathway+.%0D%0A%3Fpathway+a+wp%3APathway+%3B%0D%0Adc%3Aidentifier+%3Fwp_id+%3B%0D%0Awp%3AorganismName+%22Homo+sapiens%22%5E%5Exsd%3Astring+.%0D%0A%7D&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on")
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

        compound ["wp_reference"] = wp_reference(compound ["pw_id"])
        compound ["pubchem_reference"] = pc_reference(compound ["pubchem"])
        compounds.append(compound)

    return compounds

found_in_taxon_Qualifier = PBB_Core.WDItemID(value='Q15978631', prop_nr='P703', is_qualifier=True)
logincreds = PBB_login.WDLogin(<wikidatausername>, os.environ['wikidataApi'])

wp_metabolites = getMetabolitesFromWP()
for metabolite in wp_metabolites:
    pprint.pprint(metabolite)
    prep = dict()
    # instance of P31
    prep["P31"] = [PBB_Core.WDItemID(value='Q407595', prop_nr='P279', references=[copy.deepcopy(metabolite["wp_reference"])], qualifiers=[found_in_taxon_Qualifier])]
    # PubChem ID (CID) P662
    prep["P662"] = [PBB_Core.WDString(value=metabolite["pubchem"], prop_nr='P662', references=[copy.deepcopy(metabolite["wp_reference"])])]
    # Canonical SMILES P233
    prep["P233"] = [PBB_Core.WDString(value=metabolite["pubchem"], prop_nr='P233', references=[copy.deepcopy(metabolite["pubchem_reference"])])]
    # InChI P234
    prep["P234"] = [PBB_Core.WDString(value=metabolite["pubchem"], prop_nr='P234', references=[copy.deepcopy(metabolite["pubchem_reference"])])]
    # InChIKey P235
    prep["P235"] = [PBB_Core.WDString(value=metabolite["pubchem"], prop_nr='P235', references=[copy.deepcopy(metabolite["pubchem_reference"])])]
    data2add = []
    for key in prep.keys():
        for statement in prep[key]:
            data2add.append(statement)
    wdPage = PBB_Core.WDItemEngine(item_name=metabolite["metabolite_label"], data=data2add, server="www.wikidata.org",
                                           domain="drugs")
    output = wdPage.get_wd_json_representation()
    pprint.pprint(output)
    sys.exit()

