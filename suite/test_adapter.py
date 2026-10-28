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


def short_circuit_document(language):
    # Independent transport example, not serialized from either producer.
    def fact(v): return {'status':'known','value':v}
    key = 'gstyle.go:guards' if language == 'go' else 'compat.rust.hir-r0:guards'
    def node(identity,category,attributes):
        attributes = dict(attributes)
        if language == 'go': attributes['extensions'] = {'gstyle.value:basic':'bool'}
        return {'id':identity,'category':category,'attributes':attributes,
                'evidence':{'status':'supported'},'annotations':{'compat.rust.hir-r0:type':fact('bool')}}
    def edge(identity,source,target,kind,subkind,**attrs):
        return {'id':identity,'source':source,'target':target,'kind':kind,'subkind':subkind,
                'evidence':{'status':'supported'},**attrs}
    return {
        'function':{'inputs':[{'position':i,'symbol_id':s,'type':fact('bool'),'variadic':fact(False)}
                              for i,s in enumerate(('a','b'))],
                    'outputs':[{'position':0,'role':'return','type':fact('bool'),'variadic':fact(False)}]},
        'symbols':[{'id':s,'role':'parameter','type':fact('bool')} for s in ('a','b')],
        'definitions':[{'id':'d'+s,'symbol_id':s,'node_id':'f'+s} for s in ('a','b')],
        'nodes':[node('f'+s,'formal_input',{'position':i,'symbol_ids':[s],'defines':['d'+s]}) for i,s in enumerate(('a','b'))]
                + [node('r'+s,'read',{'symbol_ids':[s],'reads':[{'symbol_id':s,'operand_position':0}]}) for s in ('a','b')]
                + [node('p','control',{'construct':'&&','outcomes':['true','false']}),
                   node('m','merge',{}),node('ret','return',{'exit_kind':'normal'})],
        'edges':[edge('rd'+s,'f'+s,'r'+s,'data','reaching_definition',operand_position=0,
                      symbol_id=s,definition_id='d'+s,loop_carried=False) for s in ('a','b')]
                + [edge('test','ra','p','data','value_operand',operand_position=0),
                   edge('right','rb','m','data','value_alternative',operand_position=0,outcome='true',
                        annotations={key:[[{'controller_pdg_node_id':'p','outcome':'true'}]]}),
                   edge('left','ra','m','data','value_alternative',operand_position=1,outcome='false',
                        annotations={key:[[{'controller_pdg_node_id':'p','outcome':'false'}]]}),
                   edge('result','m','ret','data','value_operand',operand_position=0),
                   edge('control','p','rb','control','postdominance',outcome='true'),
                   edge('e1','ra','p','execution','nearest_dominating_operation'),
                   edge('e2','p','rb','execution','nearest_dominating_operation'),
                   edge('e3','p','ret','execution','nearest_dominating_operation')]
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

    def test_explicit_guard_namespaces_preserve_selection(self):
        for language in ('go','rust'):
            with self.subTest(language=language):
                doc = short_circuit_document(language)
                self.assertIsNotNone(equivalent(case('short_circuit'),normalize(doc,language)))
                key = 'gstyle.go:guards' if language == 'go' else 'compat.rust.hir-r0:guards'
                doc['edges'][3]['annotations'][key][0][0]['controller_pdg_node_id'] = 'ra'
                self.assertIsNone(equivalent(case('short_circuit'),normalize(doc,language)))
                doc = short_circuit_document(language)
                del doc['edges'][3]['annotations']
                with self.assertRaises(Incomplete): normalize(doc,language)

    def test_go_guards_on_ordinary_operands_are_rejected(self):
        doc = identity_document()
        doc['edges'][1]['annotations'] = {'gstyle.go:guards': []}
        with self.assertRaises(Incomplete): normalize(doc,'go')

    def test_duplicate_dependencies_remain_distinct(self):
        doc = identity_document(); extra = copy.deepcopy(doc['edges'][0]); extra['id']='rd2'; doc['edges'].append(extra)
        self.assertIsNone(equivalent(case('identity'),normalize(doc,'rust')))


if __name__ == '__main__': unittest.main()
