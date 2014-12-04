# ProteinBoxBot: Human genes #

This folder contains the different python scripts used to add, edit and update human genes in WikiData. 

## ProteinBoxBotFunctions.py ##
ProteinBoxBotFunctions.py is a core library in the different bots adding, editing and updating human genes in WikiData.

## ProteinBoxBotKnowledge.py ##
ProteinBoxBotKnowledge.py contains static links to WikiData entries. 

## Individual bots ##

###addEntrezGene2WD.py###
This bot is a custom made bot to add Entrez Gene entries in WikiData. It is a result of the https://www.wikidata.org/wiki/User:ProteinBoxBot/201408_sprint

Usage: python addEntrezGene2WD.py <toImport.txt>
   toImport.txt: a list of entrez genes to be added.

###ProteinBoxBotTemplate.py###
This bot acts as a bot template to create stubs for a resource to be added. 

Usage: Usage: python ProteinBoxBoxTemplate.py <fileNameWithIds> <WikiDataResourceID> <WikiDataTypeID> 

#### fileNameWithIds ####
  The file should contain (separated by '\t')
  1. Globally unique identifier (required)
  2. Wikidata property of the Global identifier (required)
  3. A label (required)
  4. A description (optional)

#### WikiDataResourceID ####
The WikiDataResourceID is the identifier to the WikiData entry of the Datasource under scrutiny. E.g. when an entry for Ensembl gene release 76 is added, the WikiDataResourceID = [Q17934957](https://www.wikidata.org/wiki/Q17934957)

#### WikiDataTypeID ####
The WikiDataTypeID is the identifier to the WikiData entry of the semantic type of the entry. E.g. when a resource entry reflects a Gene, the WikiDataTypeID = [Q7187](https://www.wikidata.org/wiki/Q7187)

To add Ensembl release 76 to WikiData the following steps are needed:
1. Prepare the input file (fileNameWithIds)
2. Run the command: **python ProteinBoxBoxTemplate.py <fileNameWithIds> Ensembl.tsv Q17930849 Q7187**

