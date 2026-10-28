"""Handwritten transport input checks: missing evidence cannot become a pass."""
import copy
import unittest

from adapter import Incomplete, normalize
from expectations import case
from graph import equivalent


def identity_document():
    def fact(value): return {'status':'known','value':value}
    def node(identity, category, attributes):
        return {'id':identity,'category':category,'attributes':attributes,
                'evidence':{'status':'supported'},
                'annotations':{'compat.rust.hir-r0:type':fact('i32')}}
    def edge(identity,source,target,kind,subkind,**attrs):
        return {'id':identity,'source':source,'target':target,'kind':kind,'subkind':subkind,
                'evidence':{'status':'supported'},**attrs}
    return {
        'function':{'inputs':[{'position':0,'symbol_id':'a','type':fact('i32'),'variadic':fact(False)}],
                    'outputs':[{'position':0,'role':'return','type':fact('i32'),'variadic':fact(False)}]},
        'symbols':[{'id':'a','role':'parameter','type':fact('i32')}],
        'definitions':[{'id':'da','symbol_id':'a','node_id':'fa'}],
        'nodes':[node('fa','formal_input',{'position':0,'symbol_ids':['a'],'defines':['da']}),
                 node('ra','read',{'symbol_ids':['a'],'reads':[{'symbol_id':'a','operand_position':0}]}),
                 node('ret','return',{'exit_kind':'normal'})],
        'edges':[edge('rd','fa','ra','data','reaching_definition',operand_position=0,
                      symbol_id='a',definition_id='da',loop_carried=False),
                 edge('v','ra','ret','data','value_operand',operand_position=0),
                 edge('ex','ra','ret','execution','nearest_dominating_operation')]
    }


class AdapterTests(unittest.TestCase):
    def test_independent_transport_input(self):
        self.assertIsNotNone(equivalent(case('identity'),normalize(identity_document(),'rust')))

    def test_missing_positions_and_loop_evidence_do_not_match(self):
        for field,index in [('operand_position',0),('operand_position',1),('loop_carried',0)]:
            with self.subTest(field=field,index=index):
                doc = identity_document(); del doc['edges'][index][field]
                graph = normalize(doc,'rust')
                self.assertTrue(graph.issues)
                self.assertIsNone(equivalent(case('identity'),graph))

    def test_conflicting_type_binding_guard_and_evidence_rejected(self):
        bad = []
        doc = identity_document(); doc['nodes'][1]['annotations']['compat.rust.hir-r0:type']['value']='bool'; bad.append(doc)
        doc = identity_document(); doc['nodes'][1]['attributes']['symbol_ids']=['other']; bad.append(doc)
        doc = identity_document(); doc['edges'][1]['annotations']={'compat.rust.hir-r0:guards':[]}; bad.append(doc)
        doc = identity_document(); doc['edges'][0]['evidence']['status']='unknown'; bad.append(doc)
        for index,doc in enumerate(bad):
            with self.subTest(index=index), self.assertRaises(Incomplete): normalize(doc,'rust')

    def test_duplicate_dependencies_remain_distinct(self):
        doc = identity_document(); extra = copy.deepcopy(doc['edges'][0]); extra['id']='rd2'; doc['edges'].append(extra)
        self.assertIsNone(equivalent(case('identity'),normalize(doc,'rust')))


if __name__ == '__main__': unittest.main()
