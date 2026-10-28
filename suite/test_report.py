"""Independent gate checks: incomplete evidence and missing results stay failures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from expectations import CASES
from report import REQUIRED_CAPABILITIES, checks, evidence_gaps, write_report


def passing_summary():
    producer = {'status':'pass', 'schema':'pass', 'evidence_status':'pass',
                'source_content':{'status':'pass'}, 'source_correspondence':{'status':'pass'},
                'producer_evidence':{'capabilities':{c:{'status':'supported'} for c in REQUIRED_CAPABILITIES},
                                     'conformance':{'status':'conformant'}}}
    return {name:{'original':{'go':copy.deepcopy(producer),'rust':copy.deepcopy(producer),'cross_language':'pass'},
                  'renamed':{'go':copy.deepcopy(producer),'rust':copy.deepcopy(producer),'cross_language':'pass'},
                  'invariance':{'go':'pass','rust':'pass'},'execution':{'status':'pass'}} for name in CASES}


class ReportingTests(unittest.TestCase):
    def test_complete_pass_and_nonpassing_checks_in_json_and_markdown(self):
        summary = passing_summary()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            self.assertEqual(write_report(path,summary)['status'],'pass')
            self.assertEqual(json.loads((path/'failures.json').read_text())['failures'],[])
            mutations = [summary['branch']['original']['go'],summary['branch']['renamed']['rust']]
            mutations[0]['status'] = 'fail'
            mutations[1]['source_correspondence'] = {'status':'fail','reason':'shifted | span\nwrong bytes'}
            summary['identity']['original']['cross_language'] = 'fail'
            summary['chain']['invariance']['go'] = 'fail'
            summary['early']['execution']['status'] = 'fail'
            outcome = write_report(path,summary)
            self.assertEqual(outcome['nonpassing'],5)
            failures = json.loads((path/'failures.json').read_text())['failures']
            self.assertEqual({f['check'] for f in failures},
                             {'graph','source_correspondence','cross_language','invariance','execution'})
            self.assertIn('shifted \\| span wrong bytes',(path/'report.md').read_text())

    def test_evidence_limits_block_even_when_all_graphs_pass(self):
        summary = passing_summary()
        producer = summary['branch']['original']['go']
        producer['producer_evidence']['capabilities']['node_extraction'] = {'status':'approximated','description':'partial lowering'}
        producer['producer_evidence']['conformance'] = {'status':'non_conformant','reasons':['incomplete dependencies']}
        failures = [r for r in checks(summary) if r['status'] != 'pass']
        self.assertEqual(len(failures),1)
        self.assertEqual(failures[0]['status'],'incomplete')
        self.assertIn('node_extraction=approximated',failures[0]['reason'])
        self.assertIn('incomplete dependencies',failures[0]['reason'])
        self.assertEqual(producer['status'],'pass')
        del producer['producer_evidence']['capabilities']['returns']
        self.assertTrue(any('returns=missing' in gap for gap in evidence_gaps(producer['producer_evidence'])))

    def test_unsupported_missing_schema_and_infrastructure_never_pass(self):
        summary = passing_summary()
        summary['branch']['original']['go']['status'] = 'unsupported'
        del summary['identity']['renamed']['rust']['schema']
        del summary['chain']
        with tempfile.TemporaryDirectory() as temporary:
            outcome = write_report(temporary,summary,{'reason':'compiler missing'})
            self.assertEqual(outcome['status'],'fail')
            self.assertEqual(outcome['by_status']['unsupported'],1)
            self.assertGreater(outcome['by_status']['not_run'],1)
            failures = json.loads((Path(temporary)/'failures.json').read_text())['failures']
            self.assertTrue(any(f['check'] == 'infrastructure' for f in failures))


if __name__ == '__main__':
    unittest.main()
