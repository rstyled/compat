"""Independent comparator tests, including count/degree-preserving corruptions."""
import copy
import random
import itertools
from collections import Counter
import unittest

from expectations import CASES, case
from graph import Graph, equivalent


class ComparatorTests(unittest.TestCase):
    def test_arbitrary_ids_and_collection_order(self):
        for name in CASES:
            with self.subTest(name=name):
                g = case(name); h = Graph()
                ids = list(g.nodes); random.Random(17).shuffle(ids)
                names = {n:'opaque:' + str(i) for i,n in enumerate(ids)}
                for n in ids: h.node(names[n],copy.deepcopy(g.nodes[n]))
                h.edges = [(names[s],names[t],copy.deepcopy(l)) for s,t,l in reversed(g.edges)]
                self.assertIsNotNone(equivalent(g,h))

    def test_corruptions(self):
        g = case('branch')
        def altered_node(entity,field,value):
            h = copy.deepcopy(g)
            n = next(n for n,l in h.nodes.items() if l.get('entity') == entity and field in l)
            h.nodes[n][field] = value
            return h
        changes = {
            'literal':altered_node('operation','literal','99'),
            'type':altered_node('binding','type','bool'),
            'parameter_position':altered_node('operation','position',9),
            'operand_position':altered_node('dependency','position',9),
            'branch_outcome':altered_node('dependency','outcome','neither'),
            'edge_family':altered_node('dependency','kind','wrong'),
            'edge_refinement':altered_node('dependency','subkind','wrong'),
            'write_form':altered_node('operation','write_form','wrong'),
        }
        h = copy.deepcopy(g); h.edges.pop(); changes['missing_edge'] = h
        h = copy.deepcopy(g); h.edges.append(h.edges[0]); changes['duplicate_edge'] = h
        h = copy.deepcopy(g); s,t,l = h.edges[0]; h.edges[0] = (t,s,l); changes['direction'] = h
        h = copy.deepcopy(g)
        i = next(i for i,(s,t,l) in enumerate(h.edges) if s == 'rx' and l == {'access':'read','position':0})
        s,t,l = h.edges[i]; h.edges[i] = (s,'s:a',l); changes['wrong_binding'] = h
        h = copy.deepcopy(g)
        i = next(i for i,(s,t,l) in enumerate(h.edges) if t == 'd:w1' and l == 'definition')
        s,t,l = h.edges[i]; h.edges[i] = (s,'d:d0',l); changes['killed_definition'] = h
        h = copy.deepcopy(g); h.node('extra',{'entity':'operation','category':'merge'}); changes['extra_merge'] = h
        for name,h in changes.items():
            with self.subTest(name=name): self.assertIsNone(equivalent(g,h))

    def test_same_counts_labels_degrees_are_insufficient(self):
        g = Graph(); h = Graph()
        for i in range(6): g.node(str(i),{'same':True}); h.node(str(i),{'same':True})
        for i in range(6): g.edge(str(i),str((i+1)%6),'e')
        for base in (0,3):
            for i in range(3): h.edge(str(base+i),str(base+(i+1)%3),'e')
        self.assertIsNone(equivalent(g,h))

    def test_parallel_edge_label_multiplicity(self):
        g = Graph(); h = Graph()
        for x in (g,h): x.node('a',{'n':0}); x.node('b',{'n':1})
        g.edge('a','b','x'); g.edge('a','b','x'); g.edge('a','b','y')
        h.edge('a','b','x'); h.edge('a','b','y'); h.edge('a','b','y')
        self.assertIsNone(equivalent(g,h))

    def test_missing_reference_rejected(self):
        g = case('identity'); g.edge('ra','missing','binding')
        with self.assertRaises(ValueError): equivalent(g,g)

    def test_agrees_with_exhaustive_small_graphs(self):
        rng = random.Random(42)
        def brute(a,b):
            for perm in itertools.permutations(b.nodes):
                m = dict(zip(a.nodes,perm))
                if any(a.nodes[n] != b.nodes[m[n]] for n in a.nodes): continue
                if Counter((m[s],m[t],l) for s,t,l in a.edges) == Counter(b.edges): return True
            return False
        for iteration in range(80):
            a = Graph(); b = Graph()
            for n in range(4):
                a.node(str(n),{'kind':rng.randrange(2)})
                b.node(str(n),{'kind':rng.randrange(2)})
            for g in (a,b):
                for _ in range(rng.randrange(9)):
                    g.edge(str(rng.randrange(4)),str(rng.randrange(4)),str(rng.randrange(2)))
            if iteration % 3 == 0: b = copy.deepcopy(a)
            with self.subTest(iteration=iteration):
                self.assertEqual(equivalent(a,b) is not None,brute(a,b))

    def test_empty_and_self_loop(self):
        self.assertEqual(equivalent(Graph(),Graph()),{})
        g = Graph(); g.node('n',{'node':1}); g.edge('n','n','loop')
        self.assertIsNotNone(equivalent(g,copy.deepcopy(g)))
        h = copy.deepcopy(g); h.edges.append(h.edges[0])
        self.assertIsNone(equivalent(g,h))


if __name__ == '__main__': unittest.main()
