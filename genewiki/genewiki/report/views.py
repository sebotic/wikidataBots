from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext

from genewiki.report.queries import get_genes, get_proteins, get_diseases, get_compounds, get_mspecies, get_mgenes, get_mproteins

def counts(request):
    genes = get_genes()
    proteins = get_proteins()
    disease_ontology = get_diseases()
    compounds = get_compounds()
    microbial_species = get_mspecies
    microbial_genes = get_mgenes
    microbial_proteins = get_mproteins
 
    vals = {'genes': genes,
            'proteins': proteins,
            'disease_ontology': disease_ontology,
            'compounds': compounds,
            'microbial_species': microbial_species,
            'microbial_genes': microbial_genes,
            'microbial_proteins': microbial_proteins,}
   
    return render(request, 'report/stats.jade', vals)
