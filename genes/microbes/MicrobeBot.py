__author__ = 'timputman'
import csv
import requests
import urllib.request
import pprint
import sys
import PBB_Core
import PBB_login
from collections import defaultdict
import ast
import gzip
import time
from time import gmtime, strftime

login = PBB_login.WDLogin(sys.argv[3], sys.argv[4])


class WDLabel2QID(object): # This is where i left off...current label finder is not specific
    def __init__(self,label=''):
        self.qid = self.get_items_qid_by_label(label)

    def get_items_qid_by_label(self, label):

        url = 'https://{}/w/api.php'.format("www.wikidata.org")
        params = {
            'action': 'wbsearchentities',
            'language': 'en',
            'search': label,
            'format': 'json'
        }
        qidout = []
        try:
            reply = requests.get(url, params=params)
            replyjson = reply.json()
            return replyjson
            #qidout.append(replyjson['search'][0]['id'])
        except:
            qidout.append('None')

        #return qidout[0]


class WDQID2Label(object):
    def __init__(self, qid=''):
        """
        Gets all WikiData item label using qid
        :param wdquery: A string representation of a WD query
        :return: A Python json representation object with the search results is returned
        """
        self.qid = qid
        self.label = self.get_items_label_by_QID(qid)

    def get_items_label_by_QID(self, qid):
        url = 'https://www.wikidata.org/w/api.php/'
        param = dict(action='wbgetentities', props='labels', ids=qid, format='json')
        reply = requests.get(url, params=param)
        resp = reply.json()
        out = []
        try:
            eng_label = resp['entities'][qid]['labels']['en']['value']
            out.append(eng_label)
        except:
            out.append('None')
        return out[0]


class WDProp2QID(object):
    def __init__(self, string='', prop=''):
        """
        Gets all WikiData item IDs that contains statements containing property 'prop' (integer omitting the p)
        with value 'string'
        :param wdquery: A string representation of a WD query
        :return: A Python json representation object with the search results is returned
        """
        self.string = string
        self.prop = prop
        self.qid = self.get_items_QID_by_property(string,prop)

    def get_items_QID_by_property(self, string, prop):
        url = 'http://wdq.wmflabs.org/api'
        wdquery = "string[{}:\"{}\"]".format(prop, string)
        reply = requests.get(url, params={'q': wdquery})
        a = reply.json()
        out = []
        try:
            qidout = "Q" + str(a['items'][0])
            out.append(qidout)
        except:
            out.append("None")
        return str(out[0])


class NCBIReferenceGenomoes(object):
    def __init__(self):
        self.tid_list = self.get_ref_microbe_taxids()

    def get_ref_microbe_taxids(self):
        """
        Download the latest bacterial genome assembly summary from the NCBI genome ftp site
        and generate a list of relevant data for strain items based on taxids of the bacterial reference genomes.

        :return:
        """
        assembly = urllib.request.urlopen("ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt")
        datareader = csv.reader(assembly.read().decode().splitlines(), delimiter="\t")

        all_strain_data = []
        for row in datareader:
            org = row[7].split()
            strain = " ".join(org[2:])
            if row[4] == 'reference genome':
                strain_data = [row[6], row[5], row[7], strain]
                all_strain_data.append(strain_data)
        chlam = []
        for thing in all_strain_data:

            if thing[1] == '471472': # This is a testing filter to restrict bot run to chlamydia only
                return [thing]
        #return all_strain_data


class WDStrainItem(object):
    def __init__(self, ref_orgs):

        self.login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
        self.ref_orgs = ref_orgs

    def wd_strain_genome_items(self):
        """
        Generate item for each bacterial strain in wikidata
        :return:
        """
        genomes = list(self.ref_orgs)

        description = "bacterial strain"

        for i in genomes:

            try:
                item_name = i[2]
                alias = [i[-1]]
                spec_tid = str(i[0])
                parent_qid = WDProp2QID(spec_tid, '685')
                parent_taxon = PBB_Core.WDItemID(value=parent_qid.qid, prop_nr='P171')
                tid = str(i[1])
                taxid = PBB_Core.WDString(value=tid, prop_nr='P685')
                taxonname = PBB_Core.WDString(value=i[2], prop_nr='P225')
                instance_of = PBB_Core.WDItemID(value='Q855769', prop_nr='P31')
                wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=[taxid, taxonname,
                                                                                            parent_taxon,
                                                                                             instance_of])
                wd_item.set_aliases(alias)
                wd_item.set_description(description)
                pprint.pprint(wd_item.get_wd_json_representation())
                wd_item.write(self.login)

            except IndexError:
                print("{} didn't have a parent".format(i[2]))

    def wd_species_items(self):
        species = list(self.ref_orgs)
        description = "species of prokaryote"

        for i in species:
            species_all = i[2].split(" ")
            species = " ".join(species_all[0:2])
            item_name = species
            alias = [i[-1]]
            spec_tid = str(i[0])
            species_taxid = PBB_Core.WDString(value=spec_tid, prop_nr='P685')
            taxonname = PBB_Core.WDString(value=species, prop_nr='P225')
            instance_of = PBB_Core.WDItemID(value='Q16521', prop_nr='P31')
            wd_item = PBB_Core.WDItemEngine(item_name=item_name, domain='genomes', data=[species_taxid, taxonname,
                                                                                         instance_of])
            wd_item.set_aliases(alias)
            wd_item.set_description(description)
            pprint.pprint(wd_item.get_wd_json_representation())
            #wd_item.write(self.login)


class WDGeneProteinItemDownload(object):
    def __init__(self, ref_orgs):
        self.ref_orgs = ref_orgs
        self.mgi_genes = self.gain_refseq_mgi()
        self.wd_dict = self.wd_parse_mgi()
        self.uniprot_go = self.download_taxon_protein_GO()
        self.uiprot_dict = self.parse_uniprot_data()
        self.combo_mu = self.combine_mgi_uniprot_dicts()

    def gain_refseq_mgi(self):
        """
        Query mygene.info by tax id.  Return all gene records for every taxid entered in json
        :return:
        """

        url = 'http://mygene.info/v2/query/'

        genomes = list(self.ref_orgs)

        for i in genomes:
            tax_list = []
            orgidl = i[1]
            params = dict(q="__all__", species=orgidl, entrezonly="true", size="1000", fields="all")
            r = requests.get(url, params)
            tax_list.append(r.json())
            return tax_list # Yield will return a list for each taxid

    def wd_parse_mgi(self):
        """
        Go through the mygene.info json and format label and description names for genes.
        Generate gene items using PBB_Core.wd_item_enging()

        :param genes_json:
        :return:
        """
        content = self.mgi_genes
        hits = content[0]['hits']
        mgi_data = []
        for i in hits:
            if i['type_of_gene'] != 'protein-coding':
                continue
            else:
                name = i['name'] #+ " " + i['symbol']

                try:
                    uniprot = i['uniprot']['Swiss-Prot']
                except Exception:

                    try:
                        uniprot = i['uniprot']['TrEMBL']
                    except Exception:
                        continue

                taxid = str(i['taxid'])
                strain = WDProp2QID(taxid, '685')
                strain = strain.qid
                q2label = WDQID2Label(strain)
                gene_description = "microbial gene found in " + q2label.label
                protein_description = "microbial protein found in " + q2label.label
                wd_data = {
                    '_geneid': str(i['entrezgene']),
                    'taxid': str(i['taxid']),
                    'type_of_gene': i['type_of_gene'],
                    'gene_symbol': i['symbol'],
                    'protein_symbol': i['symbol'].upper(),
                    'name': name,
                    'uniprot': uniprot,
                    'RSprotein': i['refseq']['protein'],
                    'genstart': i['genomic_pos']['start'],
                    'genstop': i['genomic_pos']['end'],
                    'strand': i['genomic_pos']['strand'],
                    'RSgenomic': i['genomic_pos']['chr'],
                    'strain': strain,
                    'gene_description': gene_description,
                    'protein_description': protein_description
                }
                mgi_data.append(wd_data)
        return mgi_data


    def download_taxon_protein_GO(self):
        """
        Downloads the latest list of human proteins from uniprot through the URL specified in mygene_info_settings
        """

        url = 'http://www.uniprot.org/uniprot/'

        genomes = list(self.ref_orgs)

        for i in genomes:
            orgidl = i[1]
            params = dict(query=('organism:' + orgidl), format='tab', columns='id,go(biological process),go(cellular component),go(molecular function)')
            r = requests.get(url, params=params)
            return r.text

    def parse_uniprot_data(self):

        content = self.uniprot_go
        datareader = csv.reader(content.splitlines(), delimiter="\t")
        uniprot_data = []

        for i in datareader:
            go_dict = {
                'Uniprotid': i[0],
                'biological_process': i[1], # biological process P682
                'cell_component': i[2], # cell component P681
                'molecular_function': i[3] # molecular function P680
            }
            uniprot_data.append(go_dict)
        return uniprot_data

    def combine_mgi_uniprot_dicts(self):
        mgi = self.wd_dict
        unip = self.uiprot_dict
        out = open('mgi_uniprot_combined_{}.dict'.format(time.time()), "w")

        result = defaultdict(dict)
        mgi_uniprot = []
        try:
            for d in mgi:
                result[d['uniprot']].update(d)
            for d in unip:
                result[d['Uniprotid']].update(d)
            for k,v in result.items():
                print(v, file=out) # This writes to a file for now.  Might be better to use pickle to load pyobj

        except:
            print(mgi, file=out)


class WDWriteGeneProteinItems(object):
    def __init__(self):
        self.dbdata = open("mgi_uniprot_combined_1445503753.042013_L2434.dict", "r")

    def write_gene_item(self):
        """
        Write gene items using dictionary from wd_parse_mgi(self):
        :return:
        """
        zwd_write_data = self.dbdata
        count = 0
        for i in zwd_write_data:
            i = i.strip()

            start = time.time()
            wd_write_data= ast.literal_eval(i)
            if '_geneid' not in wd_write_data.keys():
                continue
            else:

                alias_list = [wd_write_data['gene_symbol']]
                item_name = wd_write_data['name'] + "  " + wd_write_data['gene_symbol']
                description = wd_write_data['gene_description']

                NCBIgenerefStated = PBB_Core.WDItemID(value=20641742, prop_nr='P248', is_reference=True)
                NCBIgenerefStated.overwrite_references = True
                timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
                refRetrieved.overwrite_references = True
                uniprot_protein_reference = [[NCBIgenerefStated, refRetrieved]]

                statements = dict()
                statements['found_in'] = [PBB_Core.WDItemID(value=wd_write_data['strain'], prop_nr='P703',references=uniprot_protein_reference)] #Found in taxon
                #statements['symbol'] = [PBB_Core.WDString(value=wd_write_data['gene_symbol'], prop_nr='P353',references=uniprot_protein_reference)]
                statements['geneid'] = [PBB_Core.WDString(value=wd_write_data['_geneid'], prop_nr='P351',references=uniprot_protein_reference)]
                statements['instance'] = [PBB_Core.WDItemID(value='Q7187', prop_nr='P31', references=uniprot_protein_reference)]
                statements['genomic_start'] = [PBB_Core.WDString(value=str(wd_write_data['genstart']), prop_nr='P644', references=uniprot_protein_reference)]
                statements['genomic_stop'] = [PBB_Core.WDString(value=str(wd_write_data['genstop']), prop_nr='P645', references=uniprot_protein_reference)]

                try:
                    gene_product = WDProp2QID(wd_write_data['RSprotein'], '637')
                    gene_product = gene_product.qid
                    statements['encodes'] = [PBB_Core.WDItemID(value=gene_product, prop_nr='P688',references=uniprot_protein_reference)]
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='No protein item found {}'.format(wd_write_data['_geneid']))

                final_statements = []

                for key in statements.keys():
                    for statement in statements[key]:
                        final_statements.append(statement)

                try:
                    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=final_statements)
                    PBB_Core.WDItemEngine.log(level='INFO', message='Gene item found {}'.format(wd_write_data['_geneid'] + " " + str(count) ))

                except Exception as e:

                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item data discrepency {}'.format(wd_write_data['name']))
                    continue


                try:
                    login = PBB_login.WDLogin(sys.argv[3], sys.argv[4])
                    wd_item_gene.set_label(item_name)
                    wd_item_gene.set_description(description)
                    wd_item_gene.set_aliases(alias_list)
                    #pprint.pprint(wd_item_gene.get_wd_json_representation())
                    wd_item_gene.write(login)
                    count += 1
                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item {} written successfully'.format(wd_write_data['name']))
                    print('{} gene items written'.format(count))
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='gene item write failed {}'.format(wd_write_data['name']))
                    continue

    def write_protein_item(self):
        """
        Write protein items using dictionary from wd_parse_mgi(self):
        :return:
        """
        zwd_write_data = self.dbdata
        count = 0
        for i in zwd_write_data:

            wd_write_data = ast.literal_eval(i)
            count += 1

            if '_geneid' not in wd_write_data.keys():
                continue
            else:
                item_name = wd_write_data['name'] + " " + wd_write_data['protein_symbol']
                description = wd_write_data['protein_description']
                alias_list = [wd_write_data['protein_symbol']]

                statements = dict()

                uniprotrefStated = PBB_Core.WDItemID(value=905695, prop_nr='P248', is_reference=True)
                uniprotrefStated.overwrite_references = True

                timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                refRetrieved = PBB_Core.WDTime(str(timeStringNow), prop_nr='P813', is_reference=True)
                refRetrieved.overwrite_references = True

                uniprot_protein_reference = [[uniprotrefStated, refRetrieved]]

                try:
                    gene_item = WDProp2QID(wd_write_data['_geneid'], '351')
                    gene_item = gene_item.qid
                    if gene_item is not 'None':
                        statements['encodedby'] = [PBB_Core.WDItemID(value=gene_item, prop_nr='P702', references=uniprot_protein_reference)]
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='No gene item found {}'.format(e))
                    continue

                statements['found_in'] = [PBB_Core.WDItemID(value=wd_write_data['strain'], prop_nr='P703', references=uniprot_protein_reference)] #Found in taxon
                statements['uniprotid'] = [PBB_Core.WDString(value=wd_write_data['uniprot'], prop_nr='P352', references=uniprot_protein_reference)]
                statements['proteinid'] = [PBB_Core.WDString(value=wd_write_data['RSprotein'],prop_nr='P637')]
                statements['instance'] = [PBB_Core.WDItemID(value='Q8054', prop_nr='P31', references=uniprot_protein_reference)]
                statements['molecular_function'] = []
                statements['cell_component'] = []
                statements['biological_process'] = []

                mfcount = 0
                if wd_write_data['molecular_function']:
                    mflist = wd_write_data["molecular_function"].split(";")  # P680
                    mfdictlist = []

                    for g in mflist:
                        mfsplitlist = dict()
                        mf = g.split()
                        mfsplitlist['mfgid']=mf[-1][4:-1]
                        mfsplitlist['mfgterm']=" ".join(mf[:-1])
                        mfdictlist.append(mfsplitlist)

                        mfgoqid = WDProp2QID(string=mfsplitlist['mfgid'], prop='686').qid
                        mfgolabel = WDQID2Label(qid=mfgoqid)
                        goqid =[]

                        if mfsplitlist['mfgterm'] == mfgolabel.label:
                            goqid.append(mfgoqid)
                        else:
                            pass

                        if mfgoqid == 'None':
                            properties = list()
                            properties.append(PBB_Core.WDString(value=mfsplitlist['mfgid'], prop_nr='P686', references=uniprot_protein_reference))
                            properties.append(PBB_Core.WDItemID(value='Q14860489', prop_nr='P279', references=uniprot_protein_reference))
                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=mfsplitlist['mfgterm'], data=properties,
                                                                 domain="proteins")
                                goWdPage.set_label(mfsplitlist['mfgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([mf[-1][1:-1]])
                                #pprint.pprint(goWdPage.get_wd_json_representation())

                                goWdPage.write(login)
                                mfcount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(mfsplitlist['mfgterm'] + str(mfcount)))

                                print('MF GO Item written {}'.format(mfcount))
                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO', message='failure to write new go term item {}'.format(e))

                        else:
                            try:
                                statements['molecular_function'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P680', references=uniprot_protein_reference))
                            except Exception:
                                pass

                cccount = 0
                if wd_write_data['cell_component']:
                    cclist = wd_write_data['cell_component'].split(";")  # P681
                    ccdictlist = []

                    for g in cclist:
                        ccsplitlist = dict()
                        cc = g.split()
                        ccsplitlist['ccgid'] = cc[-1][4:-1]
                        ccsplitlist['ccgterm'] = " ".join(cc[:-1])
                        ccdictlist.append(ccsplitlist)

                        ccgoqid = WDProp2QID(string=ccsplitlist['ccgid'], prop='686').qid
                        ccgolabel = WDQID2Label(qid=ccgoqid)
                        goqid =[]
                        if ccsplitlist['ccgterm'] == ccgolabel.label:
                            goqid.append(ccgoqid)
                        else:
                            pass


                        if ccgoqid == 'None':

                            properties = list()
                            properties.append(PBB_Core.WDString(value=ccsplitlist['ccgid'],
                                              prop_nr='P686', references=uniprot_protein_reference))
                            properties.append(PBB_Core.WDItemID(value='Q5058355',
                                               prop_nr='P279', references=uniprot_protein_reference))

                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=ccsplitlist['ccgterm'], data=properties,
                                                                 references=uniprot_protein_reference, domain="proteins")
                                goWdPage.set_label(ccsplitlist['ccgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([cc[-1][1:-1]])

                                goWdPage.write(login)
                                cccount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(ccsplitlist['ccgterm'] + str(ccount)))
                                print('CC GO Item written {}'.format(cccount))
                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO',
                                                          message='failure to write new go term item {}'.format(e))
                        else:
                            try:
                                statements['cell_component'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P681',
                                                                                   references=uniprot_protein_reference))
                            except Exception:
                                pass

                bpcount = 0
                if wd_write_data['biological_process']:
                    bplist = wd_write_data['biological_process'].split(";")  # P682
                    bpdictlist = []

                    for g in bplist:
                        bpsplitlist = dict()
                        bp = g.split()
                        bpsplitlist['bpgid'] = bp[-1][4:-1]
                        bpsplitlist['bpgterm'] = " ".join(bp[:-1])
                        bpdictlist.append(bpsplitlist)

                        bpgoqid = WDProp2QID(string=bpsplitlist['bpgid'], prop='686').qid
                        bpgolabel = WDQID2Label(qid=bpgoqid)
                        goqid =[]
                        if bpsplitlist['bpgterm'] == bpgolabel.label:
                            goqid.append(bpgoqid)
                        else:
                            pass

                        if bpgoqid == 'None':
                            properties = list()
                            properties.append(PBB_Core.WDString(value=bpsplitlist['bpgid'],
                                              prop_nr='P686', references=uniprot_protein_reference))
                            properties.append(PBB_Core.WDItemID(value='Q2996394',
                                               prop_nr='P279', references=uniprot_protein_reference))

                            try:
                                goWdPage = PBB_Core.WDItemEngine(item_name=bpsplitlist['bpgterm'], data=properties,
                                                                 references=uniprot_protein_reference, domain="proteins")
                                goWdPage.set_label(bpsplitlist['bpgterm'])
                                goWdPage.set_description("Gene Ontology term")
                                goWdPage.set_aliases([bp[-1][1:-1]])

                                goWdPage.write(login)
                                bpcount += 1
                                PBB_Core.WDItemEngine.log(level='INFO', message='go term item {}'.format(bpsplitlist['bpgterm'] + str(bpcount)))
                                print('BP GO Item written {}'.format(bpcount))

                            except Exception as e:
                                PBB_Core.WDItemEngine.log(level='INFO',
                                                          message='failure to write new go term item {}'.format(e))

                        else:
                            try:
                                statements['biological_process'].append(PBB_Core.WDItemID(value=goqid[0], prop_nr='P682',
                                                                                          references=uniprot_protein_reference))

                            except Exception:
                                pass


                final_statements = []

                for key in statements.keys():
                    for statement in statements[key]:
                        final_statements.append(statement)
                        #print(key, statement.prop_nr, statement.value)



                try:
                    wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='proteins', data=final_statements)
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item {}'.format(wd_write_data['name']))

                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item data discrepency {}'.format(wd_write_data['name']))

                try:
                    wd_item_protein.set_label(item_name)
                    wd_item_protein.set_description(description)
                    wd_item_protein.set_aliases(alias_list)
                    #pprint.pprint(wd_item_protein.get_wd_json_representation())
                    wd_item_protein.write(login)
                    PBB_Core.WDItemEngine.log(level='INFO', message='protein item {} written successfully'.format(wd_write_data['name'] + " " + str(count)))
                    print('{} protein items written'.format(count))
                except Exception as e:
                    PBB_Core.WDItemEngine.log(level='INFO', message='Protein error {}'.format(e))

                    continue
class Statment_Removal(object):
    def __init__(self):
        self.dbdata = open("mgi_uniprot_combined_1445503753.042013_L2434.dict", "r")

