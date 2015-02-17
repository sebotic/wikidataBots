import pywikibot
import sys
import ProteinBoxBotFunctions
import datetime
from pywikibot.data import api
import simplejson
import json
import pprint

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

f1=open('annotations', 'r')
for annotation in f1.readlines():
  location = annotation.strip()
  # location = "/tmp/ftp.ncbi.nlm.nih.gov/genomes//Zea_mays/README_CURRENT_RELEASE"
  f=open(location, 'r')
  annotationInfo = dict()
  for line in f.readlines():
   lineparts=line.split(":")
   if len(lineparts)>2:
     annotationInfo[lineparts[0]] = lineparts[1].strip()+":"+lineparts[2].strip()
   elif len(lineparts)>1:
     annotationInfo[lineparts[0]] = lineparts[1].strip()
  wdLabel = ""
  if "ANNOTATION RELEASE NAME" in annotationInfo.keys():
     print "Wikidata label: "+annotationInfo["ANNOTATION RELEASE NAME"]
     wdLabel = annotationInfo["ANNOTATION RELEASE NAME"]
  else:
     print "wikidata label: "+annotationInfo["Release name"]
     wdLabel = annotationInfo["Release name"]
  wikidataID = None
  searchResults = ProteinBoxBotFunctions.getItems(site, wdLabel)
  token = repo.token(pywikibot.Page(repo, wdLabel), 'edit')
  wikidata=None
  if len(searchResults['search']) == 0:
     wikidata = ProteinBoxBotFunctions.createNewPage(site, token)
     print wikidata
     wikidata['entities']=dict()
     wikidata['entities'][wikidata['entity']['id']]=wikidata['entity']
     wikidata = ProteinBoxBotFunctions.addLabel(wikidata, wdLabel, wikidata['entity']['id'])
     wikidataID = wikidata['entity']['id']
  else:
    wikidataID = ProteinBoxBotFunctions.getItems(site, wdLabel)["search"][0]["id"]
    ProteinBoxBotFunctions.emptyPage(site, wikidataID, token)
    wikidata = ProteinBoxBotFunctions.getItem(site, wikidataID, "\\__")
    wikidata = ProteinBoxBotFunctions.addLabel(wikidata, wdLabel, wikidataID)
  wikidata["entities"][wikidataID]["claims"] = dict()
  timestring = ""
  if "ANNOTATION RELEASE DATE" in annotationInfo.keys():
      print "Time of publication: "+annotationInfo["ANNOTATION RELEASE DATE"]
      timestring = annotationInfo["ANNOTATION RELEASE DATE"]
  else:
      print "Time of publication: "+annotationInfo["Release date"]
      timestring = annotationInfo["Release date"]
  wikidata["entities"][wikidataID]["claims"]['P577']=dict()
  wikidata["entities"][wikidataID]["claims"]['P577']=[]
  mainsnak = dict()
  mainsnak["mainsnak"]=dict()
  wikidata["entities"][wikidataID]["claims"]['P577'].append(mainsnak)
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datatype']='time'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']=dict()
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['type']='time'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']=dict()
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['after']=0
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['before']=0
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['calendarmodel']='http://www.wikidata.org/entity/Q1985727'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['precision']=11
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['time']=datetime.datetime.strptime(timestring, "%d %B %Y").strftime('+0000000%Y-%m-%dT00:00:00Z')
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['datavalue']['value']['timezone']=0
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['property']='P577'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["mainsnak"]['snaktype']='value'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["rank"]="normal"
  wikidata["entities"][wikidataID]["claims"]['P577'][0]["type"]='statement'
  wikidata["entities"][wikidataID]["claims"]['P577'][0]['references']=[]
  wikidata["entities"][wikidataID]["claims"]['P577'][0]['references']=ProteinBoxBotFunctions.addReference(wikidata["entities"][wikidataID]["claims"]['P577'][0]["references"], 'P143', 1345229)

  if "ANNOTATION REPORT" in annotationInfo.keys():
    print annotationInfo["ANNOTATION REPORT"]
    if "http://" in annotationInfo["ANNOTATION REPORT"]:
      wikidata = ProteinBoxBotFunctions.addClaims(wikidata, 'P856', [annotationInfo["ANNOTATION REPORT"]], 'url', wikidataID, False)
    print "Official website:" + annotationInfo["ANNOTATION REPORT"]
  if "TAXID" in annotationInfo.keys():
    print "NCBI taxonomy ID: " + annotationInfo["TAXID"]
    wikidata = ProteinBoxBotFunctions.addClaims(wikidata, 'P685', [annotationInfo["TAXID"]], 'string', wikidataID, False)

  # add main subject
  searchResults2 = ProteinBoxBotFunctions.getItems(site, wdLabel.split(" Annotation Release")[0].replace("NCBI ", ""))
  if len(searchResults2["search"])>0:
     speciesWikiID = int(searchResults2["search"][0]["id"][1:])
     wikidata = ProteinBoxBotFunctions.addClaims(wikidata, 'P921', speciesWikiID, 'wikibase-entityid', wikidataID, False)
     

  wikidata.pop("success", None)
  wikidata.pop("entity", None)
  wikidata['entities'][wikidataID].pop("modified", None)
  wikidata['entities'][wikidataID].pop("lastrevid", None)
  wikidata['entities'][wikidataID].pop("ns", None)
  wikidata['entities'][wikidataID].pop("pageid", None)
  wikidata['entities'][wikidataID].pop("title", None)
  wikidata['entities'][wikidataID].pop("type", None)

  # ProteinBoxBotFunctions.prettyPrint(wikidata)
  request = api.Request(site=site,
                                  action='wbeditentity',
                                  format='json',
                                  id=wikidataID,
                                  bot=True,
                                  token=token,
                                  data=json.dumps(wikidata['entities'][wikidataID]))
            # pp.pprint(localdata)
  data = request.submit()
     
