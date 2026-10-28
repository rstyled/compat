#!/usr/bin/env python3
"""Run six independent extraction oracles; exit nonzero on observed failures.

Usage: uv run --no-project --with jsonschema python suite/run.py --gstyle ... --rstyle ...
No expectations are written or updated by this program.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from jsonschema import Draft202012Validator
from adapter import normalize, Incomplete
from expectations import CASES, case
from graph import equivalent, mismatch

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


class Run:
    def __init__(self, args):
        self.args = args
        self.out = args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.env = dict(os.environ)
        self.env['PATH'] = str(Path.home()/'.cargo/bin') + os.pathsep + self.env['PATH']
        self.commands = []
        self.schema = Draft202012Validator(json.loads((ROOT.parent/'schemas/pdg.schema.json').read_text()))
        self.pins = json.loads(args.pins.resolve().read_text())
        # Resolve the compiler through rustup for hosts other than this retained run.
        result = self.command('rustc-path', ['rustup','which','--toolchain',self.pins['rust_toolchain'],'rustc'])
        self.rustc = result.stdout.decode().strip()

    def command(self, label, argv, cwd=None, extra_env=None):
        env = dict(self.env, **(extra_env or {}))
        result = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, capture_output=True)
        prefix = self.out/'commands'/f'{len(self.commands):03d}-{label}'
        prefix.parent.mkdir(exist_ok=True)
        prefix.with_suffix('.stdout').write_bytes(result.stdout)
        prefix.with_suffix('.stderr').write_bytes(result.stderr)
        self.commands.append({'label':label,'argv':[str(a) for a in argv],
                              'cwd':str(cwd or Path.cwd()),'environment_overrides':extra_env or {},
                              'exit_code':result.returncode,'stdout':str(prefix.with_suffix('.stdout').relative_to(self.out)),
                              'stderr':str(prefix.with_suffix('.stderr').relative_to(self.out))})
        save(self.out/'commands.json',self.commands)
        return result

    def require(self, label, argv, **kwargs):
        result = self.command(label, argv, **kwargs)
        if result.returncode:
            raise RuntimeError(label + ' failed; see commands.json and commands/*.stderr')
        return result.stdout

    def build(self):
        manifests = {}
        for language, source in [('gstyle',self.args.gstyle),('rstyle',self.args.rstyle)]:
            revision = self.require(language+'-revision',['git','rev-parse','HEAD'],cwd=source).decode().strip()
            state = self.require(language+'-state',['git','status','--porcelain'],cwd=source).decode()
            if revision != self.pins[language+'_revision']:
                raise RuntimeError(language + ' revision differs from pins.json; select and review a new pin explicitly')
            manifests[language] = {'path':str(source),'revision':revision,'working_tree':state}
            if state: raise RuntimeError('Use a clean source checkout for ' + language)
        self.require('build-go',['go','build','-o',self.out/'gstyle','./cmd/gstyle'],cwd=self.args.gstyle)
        self.require('build-rust',['cargo','build','--locked','-p','rstyle-driver'],cwd=self.args.rstyle,
                     extra_env={'CARGO_TARGET_DIR':str(self.args.rust_target.resolve())})
        self.driver = self.args.rust_target.resolve()/'debug/rstyle-driver'
        for label, argv in [('go-version',['go','version']),('rust-version',[self.rustc,'-vV']),
                            ('go-env',['go','env','-json']),('rust-host',['rustc','+'+self.pins['rust_toolchain'],'--print','cfg'])]:
            manifests[label] = self.require(label,argv).decode()
        if self.pins['rustc_commit'] not in manifests['rust-version']:
            raise RuntimeError('Pinned rustc commit mismatch')
        manifests['binaries'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [self.driver,self.out/'gstyle']}
        manifests['inputs'] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(ROOT.rglob('*')) if p.is_file() and (p.parent == ROOT or 'cases' in p.relative_to(ROOT).parts) and p.suffix in ('.py','.json','.rs','.go','.mod','.md')}
        manifests['pins'] = self.pins
        manifests['compat_revision'] = self.require('compat-revision',['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
        for pattern in ('*.py','*.md','*.json'):
            for source in ROOT.glob(pattern):
                target = self.out/'harness'/source.name
                target.parent.mkdir(exist_ok=True)
                shutil.copy(source,target)
        for source in (ROOT.parent/'schemas/pdg.schema.json', ROOT.parent/'schemas/fixtures/rust-r0-extraction.json'):
            shutil.copy(source,self.out/'harness'/source.name)
        manifests['schema_sha256'] = hashlib.sha256((ROOT.parent/'schemas/pdg.schema.json').read_bytes()).hexdigest()
        manifests['configuration'] = {'edition':'2021','opt_level':0,'overflow_checks':True,
                                      'debug_assertions':True,'panic_strategy':'unwind','features':[],
                                      'cfg':[],'go_module_version':'1.26.0',
                                      'scope':'acyclic primitive scalar normal flow'}
        save(self.out/'manifest.json',manifests)
        shutil.copy(self.args.pins.resolve(), self.out/'pins.json')

    def extract(self, name, variant):
        directory = self.out/name/variant
        directory.mkdir(parents=True)
        for suffix in ('go','rs'):
            source = (ROOT/'cases'/name/('f.'+suffix)).read_text()
            if variant == 'renamed':
                replacements = {'a':'input_value','b':'decision','x':'temporary','y':'next_value',
                                'F':'Renamed','f':'renamed'}
                source = re.sub(r'\b(?:a|b|x|y|F|f)\b',lambda m:replacements[m[0]],source)
                source = '\n// Formatting and binding-name metamorphism.\n' + source.replace('\n','\n\n').replace('\t','    ')
            (directory/('f.'+suffix)).write_text(source)
        shutil.copy(ROOT/'cases'/name/'go.mod',directory/'go.mod')
        go = self.command(name+'-'+variant+'-go-extract',
                          [self.out/'gstyle','patterns','--format','pdg-json',directory/'f.go'],cwd=directory)
        rust = self.command(name+'-'+variant+'-rust-extract',
                            [self.driver,self.rustc,directory/'f.rs','--crate-name','fixture','--crate-type','lib',
                             '--edition','2021','-C','overflow-checks=yes','-C','debug-assertions=yes',
                             '-C','panic=unwind','-C','opt-level=0','--emit=metadata','-o',directory/'f.rmeta'],
                            cwd=directory,extra_env={'RSTYLE_HIR_DOCUMENT_DIR':str(directory/'rust')})
        results = {}; graphs = {}
        for language, process in [('go',go),('rust',rust)]:
            if process.returncode:
                results[language] = {'status':'not_run','reason':'producer command failed; see command logs'}
                continue
            if language == 'go':
                docs = json.loads(process.stdout)
                if len(docs) != 1: raise RuntimeError('Expected exactly one Go function')
                doc, = docs
                save(directory/'go.raw.json',doc)
            else:
                bundle = json.loads((directory/'rust/unit.evidence.json').read_text())
                # Keep producer eligibility, not a guessed success from file presence.
                save(directory/'rust.inventory.json',bundle['functions'])
                if len(bundle['functions']) != 1 or len(bundle['roots']) != 1:
                    results[language] = {'status':'unsupported','reason':'Function not published as one eligible root',
                                         'inventory':bundle['functions']}
                    continue
                root = bundle['roots'][0]
                if root is None:
                    results[language] = {'status':'unsupported','reason':'Producer did not publish a graph','inventory':bundle['functions']}
                    continue
                doc = bundle['graphs'][root]['pdg']
                save(directory/'rust.raw.json',doc)
            schema_errors = [{'path':'/'.join(map(str,e.absolute_path)),'message':e.message}
                             for e in self.schema.iter_errors(doc)]
            save(directory/(language+'.schema-errors.json'),schema_errors)
            evidence = doc['extraction_evidence']
            conformance = evidence['conformance']
            claims = conformance if isinstance(conformance,list) else [conformance]
            required_caps = ('node_extraction','parameters','returns','scalar_reaching_definitions',
                             'control_dependencies','execution_dependencies')
            supported = all(evidence['capabilities'][c]['status'] == 'supported' for c in required_caps)
            evidence_status = 'pass' if supported and claims and all(c['status'] == 'conformant' for c in claims) else 'incomplete'
            results[language] = {'eligibility': 'published_r0_root' if language == 'rust' else 'selected_' + doc['profile']['id'],
                                 'evidence_status':evidence_status, 'producer_evidence':evidence,'schema':'pass' if not schema_errors else 'fail',
                                 'schema_error_count':len(schema_errors)}
            try:
                graph = normalize(doc,language)
                graphs[language] = graph
                save(directory/(language+'.normalized.json'),graph.document())
                if name == 'branch':
                    anchors = json.loads((ROOT/'cases/branch/correspondence.json').read_text())['anchors']
                    source = (directory/('f.go' if language == 'go' else 'f.rs')).read_text()
                    source_map = {}
                    for alias,category,token,occurrence in anchors:
                        if variant == 'renamed': token = {'a':'input_value','b':'decision','x':'temporary'}.get(token,token)
                        matches = list(re.finditer(r'\b' + re.escape(token) + r'\b',source))
                        anchor = matches[occurrence-1]
                        matches = [n['id'] for n in doc['nodes'] if n['category'] == category
                                   and n.get('source_span',{}).get('start',-1) <= anchor.start()
                                   and n.get('source_span',{}).get('end',-1) >= anchor.end()]
                        if len(matches) != 1: raise Incomplete('Source correspondence ambiguous/missing for ' + alias)
                        source_map[alias] = matches[0]
                    save(directory/(language+'.source-correspondence.json'),source_map)
                oracle = case(name)
                mapping = equivalent(oracle,graph)
                results[language].update(status='pass' if mapping is not None else 'fail',issues=graph.issues)
                if mapping is not None:
                    save(directory/(language+'.correspondence.json'),mapping)
                else:
                    save(directory/(language+'.mismatch.json'),mismatch(oracle,graph))
            except (Incomplete,KeyError,ValueError) as error:
                results[language].update(status='unsupported',reason=str(error))
        if len(graphs) == 2:
            same = equivalent(graphs['go'],graphs['rust'])
            results['cross_language'] = 'pass' if same is not None else 'fail'
            if same is None: save(directory/'cross-language.mismatch.json',mismatch(graphs['rust'],graphs['go']))
        else:
            results['cross_language'] = 'not_run'
        save(directory/'result.json',results)
        return results, graphs

    def execute(self, name):
        directory = self.out/name/'execution'
        directory.mkdir(parents=True)
        vectors = [(a,b) for a in (-100,-1,0,1,100) for b in (False,True)]
        if name == 'short_circuit': vectors = [(a,b) for a in (False,True) for b in (False,True)]
        elif name not in ('branch','early'): vectors = [(a,None) for a in (-100,-1,0,1,100)]
        def text(v): return str(v).lower()
        def args(a,b): return text(a) + (', '+text(b) if b is not None else '')
        gcalls = '\n'.join(f'fmt.Println(F({args(a,b)}))' for a,b in vectors)
        rcalls = '\n'.join('println!("{}", f('+args(a,b)+'));' for a,b in vectors)
        go = (ROOT/'cases'/name/'f.go').read_text().replace('package fixture','package main\nimport "fmt"',1)
        rust = (ROOT/'cases'/name/'f.rs').read_text()
        (directory/'main.go').write_text(go+'\nfunc main() {\n'+gcalls+'\n}\n')
        (directory/'main.rs').write_text(rust+'\nfn main() {\n'+rcalls+'\n}\n')
        gc = self.command(name+'-compile-go',['go','build','-o',directory/'go.bin',directory/'main.go'])
        rc = self.command(name+'-compile-rust',[self.rustc,directory/'main.rs','--edition','2021',
                           '-C','overflow-checks=yes','-C','debug-assertions=yes','-C','panic=unwind',
                           '-C','opt-level=0','-o',directory/'rust.bin'])
        result = {'vectors':vectors,'compilation':{'go':gc.returncode,'rust':rc.returncode}}
        if gc.returncode or rc.returncode:
            result['status'] = 'not_run'
        else:
            go_result = self.command(name+'-execute-go',[directory/'go.bin'])
            rust_result = self.command(name+'-execute-rust',[directory/'rust.bin'])
            def oracle(a,b):
                if name in ('identity','chain'): return a
                if name == 'overwrite': return 1
                if name == 'branch': return 1 if b else 2
                if name == 'early': return a if b else 2
                return a and b
            expected = ''.join(text(oracle(a,b))+'\n' for a,b in vectors).encode()
            result.update(status='pass' if go_result.returncode == rust_result.returncode == 0
                          and go_result.stdout == rust_result.stdout == expected else 'fail',
                          expected=expected.decode(),go=go_result.stdout.decode(),rust=rust_result.stdout.decode())
        save(directory/'result.json',result)
        return result

    def run(self):
        self.build()
        summary = {}
        for name in CASES:
            base, basegraphs = self.extract(name,'original')
            renamed, renamedgraphs = self.extract(name,'renamed')
            invariant = {lang:('pass' if equivalent(basegraphs[lang],renamedgraphs[lang]) is not None else 'fail')
                         if lang in basegraphs and lang in renamedgraphs else 'not_run'
                         for lang in ('go','rust')}
            summary[name] = {'original':base,'renamed':renamed,'invariance':invariant,'execution':self.execute(name)}
            save(self.out/'summary.json',summary)
            print(name, 'Go:',base['go']['status'],'Rust:',base['rust']['status'],
                  'cross:',base['cross_language'],'execution:',summary[name]['execution']['status'],flush=True)
        # Full compatibility includes current shared transport schema, separately reported.
        passed = all(s[variant][lang].get('status') == 'pass'
                     and s[variant][lang].get('schema') == 'pass'
                     and s[variant][lang].get('evidence_status') == 'pass'
                     for s in summary.values() for lang in ('go','rust') for variant in ('original','renamed'))
        passed = passed and all(s['execution']['status'] == 'pass'
                                and all(v == 'pass' for v in s['invariance'].values())
                                and s['original']['cross_language'] == s['renamed']['cross_language'] == 'pass'
                                for s in summary.values())
        save(self.out/'outcome.json',{'status':'pass' if passed else 'fail',
                                    'note':'Graph, transport, producer evidence and runtime outcomes are separate in summary.json.'})
        print('Artifacts:',self.out)
        return 0 if passed else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pins',type=Path,default=ROOT/'pins.json',help='Explicit reviewed producer revisions; default retains the original baseline')
    p.add_argument('--gstyle',type=Path,required=True)
    p.add_argument('--rstyle',type=Path,required=True)
    p.add_argument('--rust-target',type=Path,default=ROOT/'.build/rust')
    p.add_argument('--out',type=Path,default=ROOT/'artifacts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    args = p.parse_args()
    args.gstyle = args.gstyle.resolve(); args.rstyle = args.rstyle.resolve()
    run = Run(args)
    try: return run.run()
    except Exception as error:
        save(run.out/'fatal.json',{'status':'not_run','reason':str(error)})
        print(str(error),file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
