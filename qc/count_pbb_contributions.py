__author__ = 'andra'
from SPARQLWrapper import SPARQLWrapper, JSON
import pprint

total_items = 0
total_triples = 0
uniprotWikiDataIds = []
sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
#############################
# human proteins
#############################
sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX reference: <http://www.wikidata.org/prop/reference/>
SELECT DISTINCT ?uniprotId WHERE {
  ?protein wdt:P279 wd:Q8054 .
  ?protein wdt:P352 ?uniprotId .
  ?protein wdt:P703 wd:Q5 .
  ?protein p:P702 ?encBy .
  ?encBy prov:wasDerivedFrom ?derivedFrom .
  ?derivedFrom reference:P248 wd:Q2629752  .
}""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()
swissprot_counts = len(results["results"]["bindings"])
total_items = total_items + swissprot_counts
print("Human proteins: " + str(swissprot_counts))

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX reference: <http://www.wikidata.org/prop/reference/>
SELECT ?uniprotId WHERE {
  ?protein wdt:P279 wd:Q8054 .
  ?protein wdt:P352 ?uniprotId .
  ?protein wdt:P703 wd:Q5 .
  ?protein ?p ?encBy .
  ?encBy prov:wasDerivedFrom ?derivedFrom .
  ?derivedFrom reference:P248 wd:Q2629752  .
}""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()
swissprot_counts = len(results["results"]["bindings"])
total_triples = total_triples + swissprot_counts
print("Human proteins triples: " + str(swissprot_counts))


###############
# Human genes
###############

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q5 .
    ?ncbigeneId prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
human_gene_counts = len(results["results"]["bindings"])
total_items = total_items + human_gene_counts
print("Human genes: " + str(human_gene_counts))

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q5 .
    ?gene ?p ?o .
    ?o prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
human_gene_counts = len(results["results"]["bindings"])
total_triples = total_triples + human_gene_counts
print("Human genes triples: " + str(human_gene_counts))

###############
# Mouse genes
###############

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q83310 .
    ?ncbigeneId prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
mouse_gene_counts = len(results["results"]["bindings"])
print("Mouse genes: " + str(mouse_gene_counts))

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q83310 .
    ?gene ?p ?o .
    ?o prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
mouse_gene_counts = len(results["results"]["bindings"])
total_triples = total_triples + mouse_gene_counts
print("Mouse gene triples: " + str(mouse_gene_counts))

########
# Microbial bacteria
########
sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q10876 .
    ?ncbigeneId prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
gene_counts = len(results["results"]["bindings"])
print("Microbial genes: " + str(gene_counts))

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT ?ncbigeneId WHERE {
    ?gene wdt:P279 wd:Q7187 .
    ?gene p:P351 ?ncbigeneId .
    ?gene wdt:P703 wd:Q10876 .
    ?gene ?p ?o .
    ?o prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P143 wd:Q20641742 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
gene_counts = len(results["results"]["bindings"])
total_triples = total_triples + gene_counts
print("Microbial gene triples: " + str(gene_counts))

########
# Diseases
########
sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?doid WHERE {
    ?disease wdt:P279 wd:Q12136 .
    ?disease p:P699 ?doid .
    ?doid prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P248 wd:Q21153264 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
disease_counts = len(results["results"]["bindings"])
total_items = total_items + disease_counts
print("Diseases: " + str(disease_counts) + " (including obsolete terms) ")

sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT ?doid WHERE {
    ?disease wdt:P279 wd:Q12136 .
    ?disease p:P699 ?doid .
    ?disease ?p ?o .
    ?o prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P248 wd:Q21153264 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
disease_counts = len(results["results"]["bindings"])
total_items = total_items + disease_counts
total_triples = total_triples + disease_counts
print("Disease triples: " + str(disease_counts) + " (including obsolete terms)")

##########
# Drugs
##########
sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?drugbankid WHERE {
    ?drug wdt:P31 wd:Q12140 .
    ?drug p:P715 ?drugbankid .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
drug_counts = len(results["results"]["bindings"])
total_items = total_items + drug_counts
print("Drugs: " + str(drug_counts))


sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT ?drugbankid WHERE {
    ?drug wdt:P31 wd:Q12140 .
    ?drug p:P715 ?drugbankid .
    ?drug ?p ?o .
    ?o prov:wasDerivedFrom ?derivedFrom .
    ?derivedFrom reference:P248 wd:Q1122544 .
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
drug_counts = len(results["results"]["bindings"])
total_triples = total_triples + drug_counts
print("Drug triples: " + str(drug_counts))
##########
# Final totals
##########
print("Total items:" + str(total_items))
print("Total triples:" + str(total_triples))