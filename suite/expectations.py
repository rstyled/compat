"""Hand-authored operation/edge oracles. Never reads a producer document.

Names are explanatory aliases, not graph labels. Edge lists are exhaustive.
See CONTRACT.md and BRANCH.md for the derivation and encoding.
"""
from graph import Graph


def case(name):
    integer = name != 'short_circuit'
    params = [('a', 'i32' if integer else 'bool')]
    if name in ('branch', 'early', 'short_circuit'):
        params.append(('b', 'bool'))
    result = 'i32' if integer else 'bool'
    g = Graph()
    g.node('output', {'entity': 'output', 'position': 0, 'role': 'return',
                      'type': result, 'variadic': False})

    def op(alias, category, **attrs):
        g.node(alias, {'entity': 'operation', 'category': category, **attrs})

    def binding(alias, ty, role):
        g.node('s:' + alias, {'entity': 'binding', 'type': ty, 'role': role})

    def definition(alias, symbol):
        g.node('d:' + alias, {'entity': 'definition'})
        g.edge('d:' + alias, alias, 'defined_at')
        g.edge('d:' + alias, 's:' + symbol, 'binding')
        g.edge(alias, 'd:' + alias, 'defines')

    def read(alias, symbol):
        op(alias, 'read')
        g.edge(alias, 's:' + symbol, {'access': 'read', 'position': 0})

    def write(alias, symbol, category):
        op(alias, category, write_form='initialization' if category == 'declaration' else 'reassignment')
        definition(alias, symbol)
        g.edge(alias, 's:' + symbol, {'access': 'write', 'position': 0})

    def lit(alias, value):
        op(alias, 'computation', operator='literal', literal=value, type=result)

    def ret(alias):
        op(alias, 'return', exit_kind='normal')

    def predicate(alias, construct='if'):
        op(alias, 'control', construct=construct, outcomes=['true', 'false'])

    def dep(source, target, kind, subkind, **attrs):
        g.dependency(source, target, kind, subkind, **attrs)

    def rd(source, target, symbol):
        dep(source, target, 'data', 'reaching_definition', position=0,
            symbol='s:' + symbol, definition='d:' + source, loop_carried=False)

    def value(source, target, position=0):
        dep(source, target, 'data', 'value_operand', position=position)

    def execute(pairs):
        for source, target in pairs:
            dep(source, target, 'execution', 'nearest_dominating_operation')

    def control(targets):
        for target, outcome in targets:
            dep('p', target, 'control', 'postdominance', outcome=outcome)

    for position, (symbol, ty) in enumerate(params):
        binding(symbol, ty, 'parameter')
        op('f' + symbol, 'formal_input', position=position, variadic=False, type=ty)
        definition('f' + symbol, symbol)

    if name == 'identity':
        read('ra', 'a'); ret('ret')
        rd('fa', 'ra', 'a'); value('ra', 'ret')
        execute([('ra', 'ret')])
    elif name == 'chain':
        for symbol in ('x', 'y'):
            binding(symbol, 'i32', 'local')
        read('ra', 'a'); op('neg1', 'computation', operator='-', type='i32')
        write('dx', 'x', 'declaration'); read('rx', 'x')
        op('neg2', 'computation', operator='-', type='i32')
        write('dy', 'y', 'declaration'); read('ry', 'y'); ret('ret')
        rd('fa', 'ra', 'a'); rd('dx', 'rx', 'x'); rd('dy', 'ry', 'y')
        for s,t in [('ra','neg1'),('neg1','dx'),('rx','neg2'),('neg2','dy'),('ry','ret')]:
            value(s,t)
        execute(list(zip(['ra','neg1','dx','rx','neg2','dy','ry'],
                         ['neg1','dx','rx','neg2','dy','ry','ret'])))
    elif name in ('overwrite', 'branch'):
        binding('x', 'i32', 'local'); read('ra', 'a')
        write('d0', 'x', 'declaration'); lit('one', '1')
        write('w1', 'x', 'assignment'); read('rx', 'x'); ret('ret')
        rd('fa', 'ra', 'a'); rd('w1', 'rx', 'x')
        value('ra', 'd0'); value('one', 'w1'); value('rx', 'ret')
        if name == 'overwrite':
            execute([('ra','d0'),('d0','one'),('one','w1'),('w1','rx'),('rx','ret')])
        else:
            read('rb', 'b'); predicate('p'); lit('two', '2')
            write('w2', 'x', 'assignment')
            rd('fb','rb','b'); rd('w2','rx','x')
            value('rb','p'); value('two','w2')
            execute([('ra','d0'),('d0','rb'),('rb','p'),('p','one'),('one','w1'),
                     ('p','two'),('two','w2'),('p','rx'),('rx','ret')])
            control([('one','true'),('w1','true'),('two','false'),('w2','false')])
    elif name == 'early':
        read('rb','b'); predicate('p'); read('ra','a'); ret('ret1')
        lit('two','2'); ret('ret2')
        rd('fb','rb','b'); rd('fa','ra','a')
        value('rb','p'); value('ra','ret1'); value('two','ret2')
        execute([('rb','p'),('p','ra'),('ra','ret1'),('p','two'),('two','ret2')])
        control([('ra','true'),('ret1','true'),('two','false'),('ret2','false')])
    elif name == 'short_circuit':
        read('ra','a'); predicate('p','short-circuit-and'); read('rb','b')
        op('m','merge', type='bool'); ret('ret')
        rd('fa','ra','a'); rd('fb','rb','b')
        value('ra','p'); value('m','ret')
        dep('rb','m','data','value_alternative',position=0,outcome='true',controller='p')
        dep('ra','m','data','value_alternative',position=1,outcome='false',controller='p')
        execute([('ra','p'),('p','rb'),('p','ret')]); control([('rb','true')])
    else:
        raise ValueError(name)
    return g


CASES = ('branch', 'identity', 'chain', 'overwrite', 'early', 'short_circuit')
