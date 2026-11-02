"""Reconcile a collected Batch response and compute paired factorial text contrasts."""
import csv
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design import HERE, RUN, read, sha, slot_id
from features import features, words

RESULTS = HERE / 'results'


def save_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        if rows:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def outcome(item, snapshot):
    if item is None:
        return 'missing', '', {}
    if item.get('error'):
        return 'request_error', '', {}
    response = item.get('response')
    if not isinstance(response, dict):
        return 'malformed', '', {}
    body = response.get('body')
    if not isinstance(body, dict):
        return ('http_error' if response.get('status_code') != 200 else 'malformed'), '', {}
    if response.get('status_code') != 200:
        return 'http_error', '', body
    choices = body.get('choices') or []
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return 'malformed', '', body
    choice = choices[0]
    message = choice.get('message')
    if not isinstance(message, dict):
        return 'malformed', '', body
    value = message.get('content')
    reply = value if isinstance(value, str) else ''
    if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
        return 'refusal', reply, body
    if choice.get('finish_reason') == 'length':
        return 'truncated', reply, body
    if choice.get('finish_reason') != 'stop' or not reply.strip():
        return 'malformed', reply, body
    if body.get('model') != snapshot:
        return 'model_mismatch', reply, body
    return 'completed', reply, body


def reconcile(protocol, run=RUN):
    receipt = read(run / 'collection.json')
    lock = read(HERE / 'design-lock.json')
    if (sha((HERE / 'features.py').read_bytes()) != lock['features_sha256']
            or sha((HERE / 'protocol.json').read_bytes()) != lock['protocol_sha256']
            or sha((run / 'requests.jsonl').read_bytes()) != lock['input_jsonl_sha256']
            or receipt['batch']['metadata']['design_sha256'] != lock['input_jsonl_sha256']):
        raise ValueError('Input or feature lock mismatch')
    expected = {slot_id(m, s): (m, s) for m in range(4096) for s in protocol['seeds']}
    returned = {}
    for filename, checksum in receipt['files'].items():
        if filename not in ('output.jsonl', 'errors.jsonl'):
            raise ValueError('Unexpected response file')
        data = (run / filename).read_bytes()
        if sha(data) != checksum:
            raise ValueError('Raw result file hash mismatch')
        for line in data.splitlines():
            item = json.loads(line)
            key = item.get('custom_id')
            if key not in expected or key in returned:
                raise ValueError('Unknown or duplicate response ID')
            returned[key] = item
    counts = receipt['batch'].get('request_counts') or {}
    if receipt['batch']['status'] == 'completed' and counts.get('total') != len(expected):
        raise ValueError('Completed provider batch has an unexpected request count')
    rows, valid = [], {}
    usage = Counter()
    fps = Counter()
    for key, (mask, seed) in expected.items():
        state, text, body = outcome(returned.get(key), protocol['model'])
        tokens = body.get('usage') or {}
        if isinstance(tokens.get('prompt_tokens'), int) and isinstance(tokens.get('completion_tokens'), int):
            if min(tokens['prompt_tokens'], tokens['completion_tokens']) < 0:
                raise ValueError('Negative usage')
            usage['input'] += tokens['prompt_tokens']
            usage['output'] += tokens['completion_tokens']
            usage['reported_slots'] += 1
            details = tokens.get('prompt_tokens_details') or {}
            if isinstance(details, dict) and isinstance(details.get('cached_tokens'), int):
                usage['cached_input_reported'] += details['cached_tokens']
        row = {'mask': mask, 'seed': seed, 'active': mask.bit_count(), 'status': state}
        if state == 'completed':
            metrics = features(text)
            tokens_in_text = words(text)
            valid[mask, seed] = {'metrics': metrics, 'text': text, 'tokens': tokens_in_text,
                                 'bigrams': set(zip(tokens_in_text, tokens_in_text[1:]))}
            row.update(metrics)
            fps[body.get('system_fingerprint') or '(unreported)'] += 1
        else:
            row.update({k: None for k in protocol['primary_metrics'] + protocol['secondary_metrics']})
        rows.append(row)
    return rows, valid, usage, fps, counts


def contrasts(protocol, data):
    fields, seeds = protocol['fields_in_bit_order'], protocol['seeds']
    measures = protocol['primary_metrics'] + protocol['secondary_metrics']
    effects, interactions, phrases = [], [], []
    phrase_n = Counter(bg for entry in data.values() for bg in entry['bigrams'])

    def effect_rows(label, groups):
        n = sum(len(g) for g in groups)
        for metric in measures:
            scale = 1 if metric == 'words' else 100
            sums = [sum(sum(sign * entry['metrics'][metric] for sign, entry in contrast)
                        for contrast in g) for g in groups]
            per_seed = {f'delta_s{s}': scale * val / len(g) if g else None
                        for s, val, g in zip(seeds, sums, groups)}
            yield {**label, 'measure': metric, 'unit': 'words' if metric == 'words' else 'pp',
                   'matched_sets': n, 'delta': scale * sum(sums) / n if n else None,
                   **per_seed, **{f'n_s{s}': len(g) for s, g in zip(seeds, groups)}}

    for i, field in enumerate(fields):
        bit = 1 << i
        groups = [[] for _ in seeds]
        phrase_diff = Counter()
        for k, s in enumerate(seeds):
            for m in range(4096):
                if m & bit or (m, s) not in data or (m | bit, s) not in data:
                    continue
                off, on = data[m, s], data[m | bit, s]
                groups[k].append(((1, on), (-1, off)))
                phrase_diff.update(on['bigrams'] - off['bigrams'])
                phrase_diff.subtract(off['bigrams'] - on['bigrams'])
        effects.extend(effect_rows({'field': field}, groups))
        n = sum(map(len, groups))
        eligible = [(bg, v) for bg, v in phrase_diff.items() if phrase_n[bg] >= 30 and v]
        for direction in (1, -1):
            ranked = sorted((pair for pair in eligible if pair[1] * direction > 0),
                            key=lambda pair: (-direction * pair[1], pair[0]))
            for bg, value in ranked[:5]:
                phrases.append({'field': field, 'direction': 'higher' if direction > 0 else 'lower',
                                'phrase': ' '.join(bg), 'reply_support': phrase_n[bg],
                                'matched_pairs': n, 'delta_pp': 100 * value / n})

    for i, j in combinations(range(len(fields)), 2):
        x, y = 1 << i, 1 << j
        groups = [[] for _ in seeds]
        for k, s in enumerate(seeds):
            for m in range(4096):
                if m & (x | y):
                    continue
                keys = [(m | x | y, s), (m | x, s), (m | y, s), (m, s)]
                if all(key in data for key in keys):
                    groups[k].append(tuple((sign, data[key]) for sign, key in zip((1, -1, -1, 1), keys)))
        interactions.extend(effect_rows({'first': fields[i], 'second': fields[j]}, groups))
    return effects, interactions, phrases


def summarize(protocol, rows, data, usage, fps, provider_counts):
    measures = protocol['primary_metrics'] + protocol['secondary_metrics']
    seeds = protocol['seeds']
    cardinality, by_seed, variation = [], [], []

    def means(subset):
        return {k: statistics.fmean(entry['metrics'][k] for entry in subset) if subset else None for k in measures}

    for k in range(13):
        subset = [v for (m, _), v in data.items() if m.bit_count() == k]
        cardinality.append({'active_fields': k, 'expected': math.comb(12, k) * 3, 'completed': len(subset), **means(subset)})
    for s in seeds:
        subset = [v for (_, seed), v in data.items() if seed == s]
        by_seed.append({'seed': s, 'expected': 4096, 'completed': len(subset), **means(subset)})
    similarities = []
    same = 0
    for m in range(4096):
        entries = [data[m, s]['tokens'] for s in seeds if (m, s) in data]
        distances = []
        agreements = 0
        for a, b in combinations(entries, 2):
            union = set(a) | set(b)
            distances.append(len(set(a) & set(b)) / len(union) if union else 1.0)
            agreements += a == b
        similarities.extend(distances)
        same += agreements
        variation.append({'mask': m, 'completed_seeds': len(entries), 'distinct_normalized': len(set(map(tuple, entries))),
                          'seed_pairs': len(distances), 'equal_pairs': agreements,
                          'mean_token_jaccard': statistics.fmean(distances) if distances else None})
    price = protocol['batch_usd_per_million']
    summary = {'expected': 12288, 'statuses': dict(Counter(r['status'] for r in rows)), 'provider_counts': provider_counts,
               'pooled': means(list(data.values())), 'fingerprints': dict(fps), 'usage': dict(usage),
               'listed_cost_usd_for_reported_usage': (usage['input'] * price['input'] + usage['output'] * price['output']) / 1e6,
               'normalized_unique_replies': len({tuple(e['tokens']) for e in data.values()}),
               'three_distinct': sum(v['completed_seeds'] == v['distinct_normalized'] == 3 for v in variation),
               'all_three_same': sum(v['completed_seeds'] == 3 and v['distinct_normalized'] == 1 for v in variation),
               'seed_pairs': len(similarities), 'equal_seed_pairs': same,
               'mean_token_jaccard': statistics.fmean(similarities) if similarities else None}
    return summary, cardinality, by_seed, variation


def main():
    p = read(HERE / 'protocol.json')
    rows, valid, usage, fps, counts = reconcile(p)
    if not valid:
        raise ValueError('No eligible responses for NLP analysis')
    effects, interactions, phrases = contrasts(p, valid)
    summary, cardinality, by_seed, variation = summarize(p, rows, valid, usage, fps, counts)
    receipt = read(RUN / 'collection.json')
    timing = receipt['batch']
    summary['run'] = {
        'requested_snapshot': p['model'], 'status': timing['status'],
        'times_utc': {k: datetime.fromtimestamp(timing[k], timezone.utc).isoformat() for k in
                      ('created_at', 'in_progress_at', 'finalizing_at', 'completed_at', 'expired_at', 'failed_at', 'cancelled_at')
                      if isinstance(timing.get(k), int)},
        'request_file_sha256': timing['metadata']['design_sha256'], 'raw_file_sha256': receipt['files']}
    RESULTS.mkdir(exist_ok=True)
    for name, table in [('slot-features', rows), ('field-contrasts', effects), ('pair-interactions', interactions),
                        ('phrases', phrases), ('field-count', cardinality), ('seeds', by_seed), ('within-mask', variation)]:
        save_csv(RESULTS / (name + '.csv'), table)
    (RESULTS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    private_csv = RUN / 'eligible-replies.csv'
    private_csv.touch(mode=0o600, exist_ok=True)
    fields = p['fields_in_bit_order']
    save_csv(private_csv, [{'mask': m, 'active': m.bit_count(),
                            'fields': ' | '.join(name for i, name in enumerate(fields) if m & (1 << i)),
                            'seed': s, 'reply': entry['text'], **entry['metrics']}
                           for (m, s), entry in valid.items()])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
