"""Independent source artifacts: fragments, UTF-8 offsets and real corruptions."""
import copy
import hashlib
import unittest

from adapter import Incomplete
from source_correspondence import correspondence, resolve_source

ANCHORS = [('fa','formal_input','a',1), ('ra','read','a',2)]


def fixture(language, prefix='// π\r\n'):
    body = 'pub fn f(/* é */ a: i32) -> i32 { return a; }'.encode('utf-8')
    original = prefix.encode('utf-8') + body + b'\r\n'
    content = body if language == 'rust' else original
    digest = hashlib.sha256(content).hexdigest()
    identity = {'status':'known','value':('sha256:' if language == 'rust' else '') + digest}
    def span(position): return {'source_id':'source','start':position,'end':position+1}
    doc = {'sources':[{'id':'source','path':'navigation-only.rs','content_identity':identity}],
           'function':{'source_span':{'source_id':'source','start':0,'end':len(content)}},
           'nodes':[{'id':'formal','category':'formal_input','source_span':span(content.index(b'a:'))},
                    {'id':'read','category':'read','source_span':span(content.index(b'a;'))}]}
    region = {'start':len(prefix.encode('utf-8')), 'end':len(prefix.encode('utf-8'))+len(body)}
    bundle = {'sources':[original.decode('utf-8')], 'roots':[0],
              'functions':[{'fn_span':copy.deepcopy(region),
                            'source':{'snapshot':0,'range':region,'digest':identity['value']}}],
              'graphs':[{'cfg':{'sources':[dict(doc['sources'][0],content=body.decode('utf-8'))]}}]}
    return doc, original, bundle


class SourceCorrespondenceTests(unittest.TestCase):
    def test_fragment_and_full_file_follow_their_own_content_identities(self):
        for language in ('go','rust'):
            for prefix in ('', '// π\r\n', '\ufeff// more formatting\r\n'):
                with self.subTest(language=language,prefix=prefix):
                    doc, original, bundle = fixture(language,prefix)
                    before = copy.deepcopy(doc)
                    content, proof = resolve_source(doc,original,language,bundle)
                    self.assertEqual(correspondence(doc,content,ANCHORS),{'fa':'formal','ra':'read'})
                    self.assertEqual(doc,before)  # No offset or graph repair.
                    self.assertEqual(proof['byte_length'],len(content))
                    self.assertEqual(proof['fixture_range']['start'],len(prefix.encode()) if language == 'rust' else 0)

    def test_shifted_and_character_offsets_still_fail(self):
        doc, original, bundle = fixture('rust')
        content, _ = resolve_source(doc,original,'rust',bundle)
        for delta in (1, len('// π\r\n'.encode()), -1):
            changed = copy.deepcopy(doc)
            changed['nodes'][0]['source_span']['start'] += delta
            changed['nodes'][0]['source_span']['end'] += delta
            with self.subTest(delta=delta), self.assertRaises(Incomplete):
                correspondence(changed,content,ANCHORS)
        changed = copy.deepcopy(doc)
        position = content.decode().index('a:')  # Character index is deliberately wrong.
        changed['nodes'][0]['source_span'].update(start=position,end=position+1)
        with self.assertRaises(Incomplete): correspondence(changed,content,ANCHORS)

    def test_digest_snapshot_cfg_and_capture_disagreements_fail(self):
        for mutation in ('identity','snapshot','cfg_content','cfg_identity','range','snapshot_ref'):
            doc, original, bundle = fixture('rust')
            if mutation == 'identity': doc['sources'][0]['content_identity']['value'] = 'sha256:wrong'
            elif mutation == 'snapshot': bundle['sources'][0] = '// changed\n' + bundle['sources'][0]
            elif mutation == 'cfg_content': bundle['graphs'][0]['cfg']['sources'][0]['content'] += ' '
            elif mutation == 'cfg_identity': bundle['graphs'][0]['cfg']['sources'][0]['content_identity'] = {'status':'known','value':'sha256:wrong'}
            elif mutation == 'range': bundle['functions'][0]['source']['range']['start'] += 1
            else: bundle['functions'][0]['source']['snapshot'] = -1
            with self.subTest(mutation=mutation), self.assertRaises(Incomplete):
                resolve_source(doc,original,'rust',bundle)
        doc, original, _ = fixture('go')
        with self.assertRaises(Incomplete): resolve_source(doc,original+b' ','go')

    def test_source_ids_bounds_utf8_and_ambiguous_anchors_fail(self):
        for mutation in ('source_id','negative','past_end','split_utf8','missing_span','ambiguous'):
            doc, original, bundle = fixture('rust')
            span = doc['nodes'][0]['source_span']
            if mutation == 'source_id': span['source_id'] = 'unknown'
            elif mutation == 'negative': span['start'] = -1
            elif mutation == 'past_end': span['end'] = len(original)+1
            elif mutation == 'split_utf8': span.update(start=original.index('é'.encode())-len('// π\r\n'.encode())+1)
            elif mutation == 'missing_span': del doc['nodes'][0]['source_span']
            else: doc['nodes'].append(dict(copy.deepcopy(doc['nodes'][0]),id='duplicate'))
            with self.subTest(mutation=mutation), self.assertRaises(Incomplete):
                content, _ = resolve_source(doc,original,'rust',bundle)
                correspondence(doc,content,ANCHORS)


if __name__ == '__main__': unittest.main()
