bpgoqidlist = []
        if self.gene_record.GO_BP:
            bpdict = {}
            

            for bpgt in self.gene_record.GO_BP:
                bpdict['go_qid'] = WDProp2QID_SPARQL(prop='P686', string= bpgt['bp_goid']).qid
                bpdict['go_label'] = WDQID2Label_SPARQL(qid=bpdict['go_qid']).label

                if bpgt['bp_goterm'] == bpdict['go_label']:
                    bpgoqidlist.append(bpdict['go_qid'])
        
        statements['cell_component'].append(PBB_Core.WDItemID(value=bpgoqidlist, prop_nr='P680', references=[copy.deepcopy(uniprot_protein_reference)]))