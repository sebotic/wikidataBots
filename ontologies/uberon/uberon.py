__author__ = 'andra'
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import PBB_Debug
from time import gmtime, strftime
import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS
import traceback

class Uberon():
    def __init__(self):
        self.start = time.time()
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        # Get all WikiData entries that contain a WikiData ID
        print("Getting all terms with a Uberon ID in WikiData")
        ubWikiData_id = dict()
        ubInWikiData = PBB_Core.WDItemList("CLAIM[1554]", "1554")
        for uberonItem in ubInWikiData.wditems["props"]["1554"]:
           ubWikiData_id[str(uberonItem[2])]=uberonItem[0] # diseaseItem[2] = Uberon identifier, diseaseItem[0] = Uberon identifier
        graph = rdflib.Graph()

        graph.parse("/Users/andra/Downloads/Andra/imports/uberon_import.owl")
        cls = URIRef("http://www.w3.org/2002/07/owl#Class")
        subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        for uberon in graph.subjects(RDF.type, cls):
            try:
                uberonVars = dict()
                uberonVars["uberon"] = uberon
                uberonVars["uberonLabel"] = graph.label(URIRef(uberon))
                uberonVars["wikidata_id"] = ubWikiData_id
                uberonVars["logincreds"] = self.logincreds
                uberonVars["start"] = self.start
                uberonVars["graph"] = graph
                uberonClass = uberonTerm(uberonVars)

            except Exception as e:
                print(traceback.format_exc())
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=uberon,
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='-',
                        duration=time.time() - self.start
                    ))


class uberonTerm(object):
    def __init__(self, object):
            self.logincreds = object["logincreds"]
            self.name = object["uberonLabel"]
            self.uberon = object["uberon"]
            self.uberon_id = self.uberon.replace("http://purl.obolibrary.org/obo/UBERON_", "")
            self.wikidata_id = object["wikidata_id"]
            self.start = object["start"]
            self.graph = object["graph"]

            subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
            print(self.uberon_id)
            print(self.name)

            refStatedIn = PBB_Core.WDItemID(value=int(doVersionID.replace("Q", "")), prop_nr='P248', is_reference=True)
            refStatedIn.overwrite_references = True
            refImported = PBB_Core.WDItemID(value=5282129, prop_nr='P143', is_reference=True)
            refImported.overwrite_references = True
            timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
            refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
            refRetrieved.overwrite_references = True
            ub_reference = [refStatedIn, refImported, refRetrieved]

            for subclass in self.graph.objects(URIRef(self.uberon), subcls):
                print(subclass.replace("http://purl.obolibrary.org/obo/UBERON_", ""))
            print("======")