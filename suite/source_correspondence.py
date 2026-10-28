"""Check spans against identified bytes, without rewriting exported offsets."""
import hashlib
import re

from adapter import Incomplete, known


def bounds(span, content):
    start, end = span['start'], span['end']
    if type(start) is not int or type(end) is not int or not 0 <= start <= end <= len(content):
        raise Incomplete(f'Source range {span} outside {len(content)} identified bytes')
    try:
        content[:start].decode('utf-8')
        content[start:end].decode('utf-8')
    except UnicodeDecodeError as error:
        raise Incomplete(f'Source range splits a UTF-8 code point: {span}') from error
    return content[start:end]


def resolve_source(doc, fixture, language, bundle=None):
    if len(doc['sources']) != 1:
        raise Incomplete('Selected fixture requires exactly one PDG source')
    source, = doc['sources']
    region = {'start':0, 'end':len(fixture)}
    content = fixture
    if language == 'rust':
        root, = bundle['roots']
        function, = bundle['functions']
        capture = function['source']
        index = capture['snapshot']
        if type(index) is not int or not 0 <= index < len(bundle['sources']):
            raise Incomplete('Invalid captured source snapshot reference')
        snapshot = bundle['sources'][index].encode('utf-8')
        if snapshot != fixture:
            raise Incomplete('Captured compiler source snapshot differs from exact fixture bytes')
        region = capture['range']
        if region != function['fn_span']:
            raise Incomplete('Captured source range disagrees with function file span')
        content = bounds(region, snapshot)
        cfg_source, = bundle['graphs'][root]['cfg']['sources']
        if (cfg_source['id'] != source['id']
                or cfg_source['content_identity'] != source['content_identity']
                or cfg_source['content'].encode('utf-8') != content
                or capture['digest'] != known(source['content_identity'])):
            raise Incomplete('PDG, CFG and captured function source identities/bytes disagree')
    elif language != 'go':
        raise Incomplete('Unknown source producer: ' + language)
    digest = hashlib.sha256(content).hexdigest()
    # Go currently exports bare SHA-256; Rust R0 requires the algorithm tag.
    expected = digest if language == 'go' else 'sha256:' + digest
    if known(source['content_identity']) != expected:
        raise Incomplete('PDG source content identity does not match the identified bytes')
    for record in [doc['function'], *doc['nodes']]:
        span = record.get('source_span')
        if span is not None:
            if span['source_id'] != source['id']:
                raise Incomplete('Span references an unknown source: ' + span['source_id'])
            bounds(span, content)
    return content, {'source_id':source['id'], 'content_identity':source['content_identity'],
                     'fixture_range':region, 'byte_length':len(content),
                     'coordinate_space':'identified source bytes; raw offsets unchanged'}


def correspondence(doc, content, anchors, renamed=False):
    text = content.decode('utf-8')
    source_id, = [source['id'] for source in doc['sources']]
    mapping = {}
    for alias, category, token, occurrence in anchors:
        if renamed:
            token = {'a':'input_value','b':'decision','x':'temporary'}.get(token,token)
        tokens = list(re.finditer(r'\b' + re.escape(token) + r'\b', text))
        if not 1 <= occurrence <= len(tokens):
            raise Incomplete(f'Missing source anchor {alias}: {token!r} occurrence {occurrence}')
        token_span = tokens[occurrence-1]
        start = len(text[:token_span.start()].encode('utf-8'))
        end = len(text[:token_span.end()].encode('utf-8'))
        candidates = [n for n in doc['nodes'] if n['category'] == category]
        matches = [n['id'] for n in candidates
                   if n.get('source_span',{}).get('source_id') == source_id
                   and n['source_span']['start'] <= start and n['source_span']['end'] >= end]
        if len(matches) != 1:
            spans = [(n['id'],n.get('source_span')) for n in candidates]
            raise Incomplete(f'Source correspondence ambiguous/missing for {alias}: '
                             f'{token!r} bytes [{start},{end}) in {source_id}; candidates {spans}')
        mapping[alias] = matches[0]
    return mapping
