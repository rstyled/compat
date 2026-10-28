"""Closed, auditable spelling conversion at the PDG export boundary.

No dependency is inferred from CFG or repaired. Extra merges remain extra.
"""
from graph import Graph


class Incomplete(ValueError):
    pass


def known(fact):
    if fact.get('status') != 'known':
        raise Incomplete('Required fact unavailable: ' + str(fact))
    return fact['value']


def ty(value):
    if value not in ('int32','i32','bool'):
        raise Incomplete('Type outside suite: ' + str(value))
    return {'int32':'i32'}.get(value,value)


def normalize(doc, language):
    g = Graph()
    g.issues = []
    symbols = {s['id']:s for s in doc['symbols']}
    definitions = {d['id']:d for d in doc['definitions']}
    nodes = {n['id']:n for n in doc['nodes']}
    for records, table in [(doc['symbols'],symbols),(doc['definitions'],definitions),(doc['nodes'],nodes)]:
        if len(records) != len(table): raise Incomplete('Duplicate record ID')
    outputs = doc['function']['outputs']
    inputs = doc['function']['inputs']
    if len(outputs) != 1 or outputs[0].get('symbol_id') or doc.get('memory_locations'):
        raise Incomplete('Expected one unnamed scalar output and no memory')
    outtype = ty(known(outputs[0]['type']))
    for p in outputs:
        g.node('output', {'entity':'output','position':p['position'],'role':p['role'],
                          'type':ty(known(p['type'])),'variadic':known(p['variadic'])})
    for s in symbols.values():
        g.node('s:' + s['id'], {'entity':'binding','role':s['role'],'type':ty(known(s['type']))})
    # Only the transport-only unnamed output slot is removed. Never splice.
    removed = set()
    for n in nodes.values():
        if n['category'] == 'formal_output':
            a = n['attributes']
            if language != 'go' or a != {'position':0}:
                raise Incomplete('Nonadministrative formal output: ' + str(n))
            removed.add(n['id'])
    for n in nodes.values():
        if n['id'] in removed: continue
        c = n['category']; a = n['attributes']
        label = {'entity':'operation','category':c}
        if n['evidence']['status'] not in ('supported','approximated'):
            raise Incomplete('Unavailable operation: ' + n['id'])
        if c == 'formal_input':
            p, = [p for p in inputs if p['position'] == a['position']]
            if a.get('symbol_ids') != [p['symbol_id']]:
                raise Incomplete('Formal input binding disagrees with interface')
            label.update(position=a['position'],variadic=known(p['variadic']),type=ty(known(p['type'])))
        elif c in ('declaration','assignment'):
            forms = {':=':'initialization','initialization':'initialization',
                     '=':'reassignment','reassignment':'reassignment'}
            label['write_form'] = forms[a['write_form']]
            if c == 'assignment' and known(a.get('operator',{'status':'known','value':a['write_form']})) != '=':
                raise Incomplete('Unexpected assignment operator')
        elif c == 'computation':
            literal = a.get('literal')
            operator = known(a['operator']) if 'operator' in a else 'literal' if literal else None
            if operator not in ('literal','-'): raise Incomplete('Unexpected operator: ' + str(operator))
            label['operator'] = operator
            if literal: label['literal'] = known(literal)
            rawtype = a.get('extensions',{}).get('gstyle.value:basic') if language == 'go' else known(n['annotations']['compat.rust.hir-r0:type'])
            if rawtype is None: raise Incomplete('Missing computation type')
            label['type'] = ty(rawtype)
        elif c == 'control':
            construct = a['construct']
            if construct == '&&': construct = 'short-circuit-and'
            if construct == 'short-circuit':
                if known(a['operator']) != '&&': raise Incomplete('Expected &&')
                construct = 'short-circuit-and'
            if construct not in ('if','short-circuit-and'):
                raise Incomplete('Unexpected control: ' + construct)
            label.update(construct=construct,outcomes=a['outcomes'])
        elif c == 'return':
            label['exit_kind'] = a.get('exit_kind','normal')
        elif c == 'merge':
            # A binding join is retained, including its synthetic definition.
            if a.get('symbol_ids'):
                label['type'] = ty(known(symbols[a['symbol_ids'][0]]['type']))
            else:
                rawtype = a.get('extensions',{}).get('gstyle.value:basic') if language == 'go' else known(n['annotations']['compat.rust.hir-r0:type'])
                label['type'] = ty(rawtype)
                if 'operator' in a and known(a['operator']) != '&&':
                    raise Incomplete('Unexpected expression merge operator')
                guards = n.get('annotations',{}).get('compat.rust.hir-r0:guards')
                if guards is not None and guards != [[]]:
                    raise Incomplete('Nonunconditional merge availability outside suite')
        elif c != 'read':
            raise Incomplete('Unsupported operation category: ' + c)
        # Redundant binding/type facts must agree; never silently discard conflicts.
        accessed = [r['symbol_id'] for field in ('reads','writes') for r in a.get(field,[])]
        if c in ('read','declaration','assignment') and 'symbol_ids' in a and a['symbol_ids'] != accessed:
            raise Incomplete('Node binding list disagrees with scalar accesses: ' + n['id'])
        if language == 'rust' and c in ('formal_input','control','return'):
            rawtype = ty(known(n['annotations']['compat.rust.hir-r0:type']))
            expected_type = label['type'] if c == 'formal_input' else 'bool' if c == 'control' else outtype
            if rawtype != expected_type: raise Incomplete('Operation type disagrees with scalar interface/role')
        if c == 'read':
            if len(accessed) != 1: raise Incomplete('Expected one binding per scalar read')
            expected_type = ty(known(symbols[accessed[0]]['type']))
            rawtype = a.get('extensions',{}).get('gstyle.value:basic') if language == 'go' else known(n['annotations']['compat.rust.hir-r0:type'])
            if ty(rawtype) != expected_type: raise Incomplete('Read type disagrees with binding')
        g.node(n['id'],label)
        for field, role in [('reads','read'),('writes','write')]:
            for access in a.get(field,[]):
                if set(access) - {'symbol_id','operand_position'} or 'symbol_id' not in access:
                    raise Incomplete('Unresolved/nonlocal access')
                # Singleton scalar read/write slot, NOT arbitrary edge positions.
                if len(a[field]) != 1: raise Incomplete('Expected singleton scalar access')
                position = access.get('operand_position',0)
                g.edge(n['id'],'s:' + access['symbol_id'],{'access':role,'position':position})
        for d in a.get('defines',[]):
            if definitions[d]['node_id'] != n['id']: raise Incomplete('Definition owner disagrees')
            g.edge(n['id'],'d:' + d,'defines')
    for d in definitions.values():
        g.node('d:' + d['id'],{'entity':'definition'})
        g.edge('d:' + d['id'],d['node_id'],'defined_at')
        g.edge('d:' + d['id'],'s:' + d['symbol_id'],'binding')
    subkinds = {'scalar-value':'value_operand','reaching-definition':'reaching_definition',
                'nearest-operation-dominator':'nearest_dominating_operation',
                'post-dominator-control':'postdominance'}
    guard_key = 'gstyle.go:guards' if language == 'go' else 'compat.rust.hir-r0:guards'
    seen_edges = set()
    for e in doc['edges']:
        if e['id'] in seen_edges: raise Incomplete('Duplicate edge ID')
        seen_edges.add(e['id'])
        if e['source'] in removed or e['target'] in removed:
            if not (e['subkind'] == 'return-value' and e['target'] in removed
                    and nodes[e['source']]['category'] == 'return' and e['operand_position'] == 0):
                raise Incomplete('Unexpected output boundary edge')
            continue
        if e['evidence']['status'] != 'supported':
            raise Incomplete('Incomplete dependency: ' + str(e))
        kind = e['kind']; subkind = subkinds.get(e['subkind'],e['subkind'])
        attrs = {}
        for field, ref in [('symbol_id','symbol'),('definition_id','definition')]:
            if field in e: attrs[ref] = ('s:' if ref == 'symbol' else 'd:') + e[field]
        if guard_key in e.get('annotations',{}) and subkind != 'value_alternative':
            raise Incomplete('Unexpected guard on nonalternative dependency')
        if 'outcome' in e and not (kind == 'control' or subkind == 'value_alternative'):
            raise Incomplete('Unexpected branch outcome on dependency')
        if kind == 'execution' and 'operand_position' in e:
            raise Incomplete('Unexpected operand position on execution edge')
        if kind == 'data':
            if subkind not in ('value_operand','reaching_definition','value_alternative'):
                raise Incomplete('Unsupported data refinement: ' + subkind)
            if 'operand_position' in e:
                attrs['position'] = e['operand_position']
            elif language == 'go' and subkind == 'reaching_definition' and nodes[e['target']]['category'] == 'read' and len(nodes[e['target']]['attributes'].get('reads',[])) == 1:
                attrs['position'] = 0
            else:
                attrs['position'] = 'unrecorded'
                g.issues.append('Missing required operand position on ' + e['id'])
            if subkind == 'reaching_definition':
                # Acyclic sources; omission is disclosed in the contract.
                attrs['loop_carried'] = e.get('loop_carried',False if language == 'go' else 'unrecorded')
                if attrs['loop_carried'] == 'unrecorded':
                    g.issues.append('Missing required loop-carried fact on ' + e['id'])
                if not {'symbol','definition'} <= attrs.keys(): raise Incomplete('Missing reaching-definition identity')
            if subkind == 'value_alternative':
                attrs['outcome'] = e['outcome']
                guards = e.get('annotations',{}).get(guard_key)
                if not guards or len(guards) != 1 or len(guards[0]) != 1:
                    raise Incomplete('Expected one short-circuit guard atom')
                atom = guards[0][0]
                if atom['outcome'] != e['outcome']: raise Incomplete('Alternative guard/outcome disagreement')
                attrs['controller'] = atom['controller_pdg_node_id']
        elif kind == 'control':
            if subkind != 'postdominance': raise Incomplete('Unsupported control refinement')
            attrs['outcome'] = e['outcome']
            if 'operand_position' in e and e['operand_position'] != {'true':0,'false':1}[e['outcome']]:
                raise Incomplete('Control ordinal/outcome disagreement')
        elif kind != 'execution' or subkind != 'nearest_dominating_operation':
            raise Incomplete('Unsupported dependency: ' + str(e))
        if e.get('location_id'): raise Incomplete('Memory dependency outside suite')
        g.dependency(e['source'],e['target'],kind,subkind,**attrs)
    g.validate()
    return g
