import json
from datetime import datetime

from ProteinBoxBot_Core import PBB_Core, PBB_login
from interproscan.WDHelper import WDHelper
from interproscan.parser import parse_interpro_xml

from .local import WDUSER, WDPASS

INTERPRO = "PXXXXX"  ## CHANGE MEEE
print("CHange interpro Property ID!!")
SERVER = "www.wikidata.org"


class IPRItem:
    """
    create wikidata item from an IPRTerm
    """
    login = None
    reference = None
    fr = {"InterPro Active Site": "Site Actif InterPro",
          "InterPro Binding Site": "Site de Liaison InterPro",
          "InterPro Conserved Site": "Site Conservé InterPro",
          "InterPro Domain": "Domaine InterPro",
          "InterPro Family": "Famille InterPro",
          "InterPro PTM": "MPT InterPro",
          "InterPro Repeat": "Répétition InterPro"}

    def __init__(self, ipr):
        self.name = ipr.name
        self.id = ipr.id
        self.description = dict()
        self.description['en'] = ipr.description
        self.description['fr'] = IPRItem.fr[ipr.description]
        self.url = "http://www.ebi.ac.uk/interpro/entry/{}".format(self.id)
        self.parent = ipr.parent  # subclass of (P279)
        self.children = ipr.children  # Will not add this property to wd
        self.contains = ipr.contains  # has part (P527)
        self.found_in = ipr.found_in  # part of (P361)
        self.short_name = ipr.short_name

        # to be created
        self.wd_item_id = None

    @classmethod
    def create_reference(cls, date, version):
        """
        Create wikidata references for interpro

        Items:
        Q3047275: InterPro

        Properties:
        stated in (P248)
        imported from (P143)
        software version (P348)
        publication date (P577)

        """
        # This same reference will be used for everything
        ref_stated_in = PBB_Core.WDItemID("Q3047275", 'P248', is_reference=True)
        ref_imported = PBB_Core.WDItemID("Q3047275", 'P143', is_reference=True)
        ref_version = PBB_Core.WDString(version, 'P348', is_reference=True)
        # TODO: This doesn't work because there is a URL in the property ???
        # ref_date = PBB_Core.WDTime(date.strftime("+%Y-%m-%dT00:00:00Z"), 'P577', is_reference=True)
        reference = [ref_stated_in, ref_imported, ref_version, ]  # ref_date]
        for ref in reference:
            ref.overwrite_references = True
        cls.reference = reference
        return reference

    def create_item(self):
        # Check if item already exists first
        wd = WDHelper()
        wd_item_id = wd.prop2qid(INTERPRO, self.id)
        if wd_item_id:
            self.wd_item_id = wd_item_id
            print("item {} already exists: {}".format(self.id, wd_item_id))
            return

        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=INTERPRO, references=[self.reference])]
        item = PBB_Core.WDItemEngine(item_name=self.name, domain=None, data=statements, server=SERVER)
        item.set_label(self.name)
        for lang, description in self.description.items():
            item.set_description(description, lang=lang)
        item.set_aliases([self.short_name, self.id])
        item.write(login=self.login)
        self.wd_item_id = item.wd_item_id

        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=self.id,
            exception_type='',
            message='created interpro item',
            wd_id=item.wd_item_id,
            duration=datetime.now()
        ))

    def create_relationships(self, ipr_wd):
        # ipr_wd is a dict ipr ID to wikidata ID mapping
        statements = []
        if self.parent:
            statements.append(
                PBB_Core.WDItemID(value=ipr_wd[self.parent], prop_nr='P279', references=self.reference))  # subclass of
        if self.contains:
            for c in self.contains:
                statements.append(
                    PBB_Core.WDItemID(value=ipr_wd[c], prop_nr='P527', references=self.reference))  # has part
        if self.found_in:
            for f in self.found_in:
                statements.append(
                    PBB_Core.WDItemID(value=ipr_wd[f], prop_nr='P361', references=self.reference))  # part of

        # write data
        item = PBB_Core.WDItemEngine(wd_item_id=self.wd_item_id, data=statements, server=SERVER)
        item.write(self.login)

        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=self.id,
            exception_type='',
            message='created interpro relationships: {}'.format([(x.prop_nr, x.value) for x in statements]),
            wd_id=item.wd_item_id,
            duration=datetime.now()
        ))


def import_interpro_items():
    """
    Main function for doing interpro item import and building interpro relationships (to each other)
    :return:
    """
    d, release_info = parse_interpro_xml()
    IPRItem.create_reference(release_info['date'], release_info['version'])
    IPRItem.login = PBB_login.WDLogin(WDUSER, WDPASS, server=SERVER)
    # Start with adding all interpro items
    ipritems = {ipr_id: IPRItem(iprdict) for ipr_id, iprdict in d.items()}
    # ipritem = next(iter(ipritems.values()))
    for ipritem in ipritems.values():
        ipritem.create_item()

    # store IPRID -> wikidata ID mapping
    ipr_wd = {iprid: ipritem.wd_item_id for iprid, ipritem in ipritems.items()}
    # Add parents
    for ipritem in ipritems.values():
        ipritem.create_relationships(ipr_wd)
    return ipr_wd


def create_protein_ipr(uniprot_id, families, has_part, reference, login):
    """
    Create interpro relationships to one protein
    :param uniprot_id: uniprot ID of the protein to modify
    :type uniprot_id: str
    :param families: list of ipr wd ids the protein is a (P279) subclass of
    :param has_part: list of ipr wd ids the protein has (P527) has part
    :return:
    """

    # Get the wikidata qid of the protein
    uniprot_wdid = WDHelper().uniprot2qid(uniprot_id)

    statements = []
    if families:
        for f in families:
            statements.append(PBB_Core.WDItemID(value=f, prop_nr='P279', references=reference))
    if has_part:
        for hp in has_part:
            statements.append(PBB_Core.WDItemID(value=hp, prop_nr='P527', references=reference))

    item = PBB_Core.WDItemEngine(wd_item_id=uniprot_wdid, data=statements, server=SERVER)
    item.write(login)

    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
        main_data_id=uniprot_id,
        exception_type='',
        message='created protein interpro relationships: {}'.format([(x.prop_nr, x.value) for x in statements]),
        wd_id=uniprot_wdid,
        duration=datetime.now()
    ))


def create_all_protein_interpro(ipr_wd=None):
    """
    Main function for creating all protein <-> interpro relationships
    :param ipr_wd: dict[interpro ID]: wikidata ID
    :return:
    """

    # if you don't pass in a interpro <-> wdID dict, get it from wikidata
    if not ipr_wd:
        ipr_wd = WDHelper().id_mapper(INTERPRO)

    # parse the interpro item info
    d, release_info = parse_interpro_xml()

    # create the reference statements
    # Same as we used for the interpro item relationships
    reference = IPRItem.create_reference(release_info['date'], release_info['version'])
    login = PBB_login.WDLogin(WDUSER, WDPASS)

    # parse the protein <-> interpro relationships
    with open("interproscan/data/interproscan_uniprot_human.json", 'r') as f:
        uni_dict = json.load(f)

    # uniprot_id = 'P28223'
    for uniprot_id in uni_dict.keys():
        items = [d[x] for x in set(x['interpro_id'] for x in uni_dict[uniprot_id])]
        # Of all families, which one is the most precise? (remove families that are parents of any other family in this list)
        families = [x for x in items if x.type == "Family"]
        families_id = set(x.id for x in families)
        parents = set(family.parent for family in families)
        # A protein be in multiple families. ex: http://www.ebi.ac.uk/interpro/protein/A0A0B5J454
        specific_families = families_id - parents
        specific_families_wd = [ipr_wd[x] for x in specific_families]

        # all other items (not family) are has part (P527)
        has_part = [x for x in items if x.type != "Family"]
        has_part_wd = [ipr_wd[x] for x in has_part]

        create_protein_ipr(uniprot_id, specific_families_wd, has_part_wd, reference, login)
