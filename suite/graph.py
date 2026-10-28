"""Exact labeled directed multigraphs, including reference incidence.

Dependency records become vertices so their symbol/definition/controller references
participate in the SAME bijection as operations. No hashes or WL are used.
"""
import json
from collections import Counter


def key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def node(self, identity, label):
        if identity in self.nodes:
            raise ValueError('Duplicate node: ' + identity)
        self.nodes[identity] = label

    def edge(self, source, target, label):
        self.edges.append((source, target, label))

    def dependency(self, source, target, kind, subkind, **attrs):
        refs = {k: attrs.pop(k) for k in ('symbol','definition','controller') if k in attrs}
        identity = 'edge:' + str(sum(n.startswith('edge:') for n in self.nodes))
        self.node(identity, {'entity':'dependency', 'kind':kind, 'subkind':subkind, **attrs})
        self.edge(identity, source, 'source'); self.edge(identity, target, 'target')
        for role, ref in refs.items():
            self.edge(identity, ref, role)

    def validate(self):
        for source, target, _ in self.edges:
            if source not in self.nodes or target not in self.nodes:
                raise ValueError(f'Dangling reference: {source} -> {target}')

    def document(self):
        return {'nodes':self.nodes, 'edges':self.edges}


def equivalent(left, right):
    """Return an exact bijection or None; signatures only prune search."""
    left.validate(); right.validate()
    if len(left.nodes) != len(right.nodes) or len(left.edges) != len(right.edges):
        return None
    def index(g):
        pairs = Counter((s,t,key(label)) for s,t,label in g.edges)
        signatures = {}
        for n,label in g.nodes.items():
            incident = Counter()
            for s,t,el in g.edges:
                if s == n: incident[('out',key(el),key(g.nodes[t]))] += 1
                if t == n: incident[('in',key(el),key(g.nodes[s]))] += 1
            signatures[n] = (key(label), tuple(sorted(incident.items())))
        return pairs, signatures
    lp, ls = index(left); rp, rs = index(right)
    candidates = {n:[m for m in right.nodes if ls[n] == rs[m]] for n in left.nodes}
    if any(not v for v in candidates.values()): return None
    edge_labels = {k for _,_,k in lp} | {k for _,_,k in rp}
    mapping = {}; used = set()
    def compatible(n,m):
        if any(lp[n,n,k] != rp[m,m,k] for k in edge_labels): return False
        return all(lp[n,a,k] == rp[m,b,k] and lp[a,n,k] == rp[b,m,k]
                   for a,b in mapping.items() for k in edge_labels)
    def search():
        if len(mapping) == len(left.nodes):
            # Independent full-multiset check: direction, labels and duplicates.
            return Counter((mapping[s],mapping[t],k) for s,t,k in lp.elements()) == rp
        remaining = {}
        for n in left.nodes.keys() - mapping.keys():
            choices = [m for m in candidates[n] if m not in used and compatible(n,m)]
            if not choices: return False
            remaining[n] = choices
        n = min(remaining, key=lambda n: (len(remaining[n]), n))
        for m in remaining[n]:
            mapping[n] = m; used.add(m)
            if search(): return True
            used.remove(m); del mapping[n]
        return False
    return dict(mapping) if search() else None


def mismatch(expected, actual):
    """Labels plus neighborhoods and raw IDs make nonisomorphism actionable."""
    ec = Counter(key(x) for x in expected.nodes.values())
    ac = Counter(key(x) for x in actual.nodes.values())
    return {'missing_labels':list((ec-ac).elements()), 'extra_labels':list((ac-ec).elements()),
            'expected':expected.document(), 'actual':actual.document(),
            'reason':'No label-preserving bijection preserves every directed edge and its multiplicity.'}
