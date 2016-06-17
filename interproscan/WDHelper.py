from SPARQLWrapper import SPARQLWrapper, JSON
"""
modified from Tim's wikidatabots/genes/microbes/MicrobeBotWDFunctions.py
"""


class WDHelper:

    def __init__(self):
        self.endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        self.wd = 'PREFIX wd: <http://www.wikidata.org/entity/>'
        self.wdt = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/>'

    def execute_query(self, query):
        self.endpoint.setQuery(query)
        self.endpoint.setReturnFormat(JSON)
        return self.endpoint.query().convert()

    def prop2qid(self, prop, string):
        """
        :param prop: 'P351' Entrez gene id (ex. print( WDHelper().prop2qid('P351','899959')))
        :param string: '899959' String value
        :return: QID Q21514037
        """
        arguments = '?gene wdt:{} "{}"'.format(prop, string)
        select_where = 'SELECT * WHERE {{{}}}'.format(arguments)
        query = self.wdt + " " + select_where
        results = self.execute_query(query)
        result = results['results']['bindings']
        if len(result) == 0:
            # not found
            return None
        elif len(result) > 1:
            raise ValueError("More than one wikidata ID found for {} {}: {}".format(prop, string, result))
        else:
            return result[0]['gene']['value'].split("/")[-1]

    def uniprot2qid(self, uniprotID):
        return self.prop2qid("P352", uniprotID)

    def id_mapper(self, prop):
        """
        Get all wikidata ID <-> prop <-> value mappings
        Example: id_mapper("P352") -> { 'A0KH68': 'Q23429083',
                                         'Q5ZWJ4': 'Q22334494',
                                         'Q53WF2': 'Q21766762', .... }
        :param prop: wikidata property
        :return:
        """
        arguments = '?gene wdt:{} ?id'.format(prop)
        select_where = 'SELECT * WHERE {{{}}}'.format(arguments)
        query = self.wdt + " " + select_where
        results = self.execute_query(query)
        if not results['results']['bindings']:
            return None
        return {x['id']['value']: x['gene']['value'].split('/')[-1] for x in results['results']['bindings']}