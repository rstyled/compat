"""One strict gate and an explicit list of every nonpassing compatibility check."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from expectations import CASES

REQUIRED_CAPABILITIES = ('node_extraction', 'parameters', 'returns',
                         'scalar_reaching_definitions', 'control_dependencies',
                         'execution_dependencies')


def evidence_gaps(evidence):
    gaps = []
    capabilities = evidence.get('capabilities', {})
    for name in REQUIRED_CAPABILITIES:
        fact = capabilities.get(name, {})
        if fact.get('status') != 'supported':
            gaps.append(f"{name}={fact.get('status', 'missing')}: {fact.get('description', 'no evidence')}")
    claims = evidence.get('conformance', [])
    if isinstance(claims, dict):
        claims = [claims]
    if not claims:
        gaps.append('conformance=missing')
    for claim in claims:
        if claim.get('status') != 'conformant':
            gaps.append(f"conformance={claim.get('status', 'missing')}: " + '; '.join(claim.get('reasons', [])))
    return gaps


def checks(summary, fatal=None):
    records = []

    def add(case, variant, producer, check, status, reason, artifact):
        records.append(dict(case=case, variant=variant, producer=producer, check=check,
                            status=status, reason=reason if status != 'pass' else '', artifact=artifact))

    for name in CASES:
        result = summary.get(name, {})
        for variant in ('original', 'renamed'):
            observed = result.get(variant, {})
            for language in ('go', 'rust'):
                record = observed.get(language, {})
                directory = f'{name}/{variant}'
                artifact = f'{directory}/result.json'
                add(name, variant, language, 'graph', record.get('status', 'not_run'),
                    record.get('reason', f'See {language}.mismatch.json and producer command logs'), artifact)
                add(name, variant, language, 'schema', record.get('schema', 'not_run'),
                    f'See {language}.schema-errors.json and producer command logs', artifact)
                gaps = evidence_gaps(record.get('producer_evidence', {}))
                evidence_status = record.get('evidence_status', 'not_run')
                # An incorrect cached status must never upgrade incomplete claims.
                if evidence_status == 'pass' and gaps:
                    evidence_status = 'incomplete'
                add(name, variant, language, 'evidence', evidence_status,
                    '; '.join(gaps) or 'See producer_evidence in result.json', artifact)
                fields = ('source_content', 'source_correspondence') if name == 'branch' else ('source_content',)
                for field in fields:
                    fact = record.get(field, {})
                    add(name, variant, language, field, fact.get('status', 'not_run'),
                        fact.get('reason', 'Required source check did not run'), artifact)
            add(name, variant, 'go+rust', 'cross_language', observed.get('cross_language', 'not_run'),
                'See cross-language.mismatch.json and producer results', f'{name}/{variant}/result.json')
        for language in ('go', 'rust'):
            add(name, 'original+renamed', language, 'invariance', result.get('invariance', {}).get(language, 'not_run'),
                'Original and renamed graphs must be exactly equivalent; see their normalized graphs', 'summary.json')
        execution = result.get('execution', {})
        add(name, 'original', 'go+rust', 'execution', execution.get('status', 'not_run'),
            'See compilation exit codes, expected/actual outputs and command logs', f'{name}/execution/result.json')
    if fatal:
        add('setup', '', '', 'infrastructure', 'not_run', fatal['reason'], 'fatal.json')
    return records


def write_report(directory, summary, fatal=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    records = checks(summary, fatal)
    failures = [r for r in records if r['status'] != 'pass']
    counts = {status:sum(r['status'] == status for r in records)
              for status in sorted({r['status'] for r in records})}
    outcome = dict(status='fail' if failures else 'pass', checks=len(records),
                   passed=counts.get('pass', 0), nonpassing=len(failures), by_status=counts)
    (directory/'failures.json').write_text(json.dumps(dict(**outcome, failures=failures), indent=2) + '\n')
    (directory/'outcome.json').write_text(json.dumps(outcome, indent=2) + '\n')
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = ['# Go/Rust compatibility: ' + outcome['status'].upper(), '',
             f"{outcome['passed']}/{outcome['checks']} checks pass; {len(failures)} nonpassing.", '',
             'Incomplete evidence, unsupported extraction and checks not run all block this gate.', '']
    manifest_path = directory/'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for language in ('gstyle', 'rstyle'):
            lines.append(f"- {language}: `{manifest[language]['revision']}`")
        lines.append('')
    if failures:
        lines += ['| Case | Variant | Producer | Check | Status | Reason | Details |',
                  '| --- | --- | --- | --- | --- | --- | --- |']
        lines += ['| ' + ' | '.join(cell(r[k]) for k in
                  ('case','variant','producer','check','status','reason','artifact')) + ' |' for r in failures]
    else:
        lines.append('No failing checks.')
    lines += ['', 'Download the run artifact for exact sources, raw outputs, configuration and mismatch details.', '']
    (directory/'report.md').write_text('\n'.join(lines))
    suite = ET.Element('testsuite', name='gstyle-rstyle-compat', tests=str(len(records)), failures=str(len(failures)))
    for record in records:
        test = ET.SubElement(suite, 'testcase', classname='compat.' + record['producer'],
                             name='/'.join(record[k] for k in ('case','variant','check')))
        if record['status'] != 'pass':
            failure = ET.SubElement(test, 'failure', type=record['status'], message=record['reason'])
            failure.text = record['artifact']
    ET.ElementTree(suite).write(directory/'junit.xml', encoding='utf-8', xml_declaration=True)
    return outcome
