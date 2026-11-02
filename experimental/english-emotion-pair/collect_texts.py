"""Reconcile private provider files to both frozen designs, then extract one row per slot."""
from collections import Counter
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import HERE, PARENT, RUN, bindings, design, read, sha
from analyze import outcome, save_csv
from measures import LISTED, measure

CASES = ('uncertain', 'embarrassed', 'happy')
RESULTS = HERE / 'results'
P = read(HERE / 'protocol.json')
PREVIOUS = read(PARENT / 'protocol.json')
FIELDS = PREVIOUS['fields_in_bit_order']
SEEDS = P['seeds']
OLD_METRICS = PREVIOUS['primary_metrics'] + PREVIOUS['secondary_metrics']
METRICS = OLD_METRICS + list(LISTED)


def consume(root, lock, keys, *, historical=False):
    receipt = read(root / 'collection.json')
    batch = receipt['batch']
    if (batch['metadata']['design_sha256'] != lock['input_jsonl_sha256']
            or sha((root / 'requests.jsonl').read_bytes()) != lock['input_jsonl_sha256']
            or batch['status'] not in ('completed', 'failed', 'expired', 'cancelled')):
        raise ValueError('Input hash or final batch status differs')
    if historical and receipt['files'].get('output.jsonl') != P['baseline_output_sha256']:
        raise ValueError('Historical response hash differs')
    if batch['status'] == 'completed' and batch['request_counts']['total'] != len(keys):
        raise ValueError('Provider total differs')
    returned = {}
    for name, checksum in receipt['files'].items():
        if name not in ('output.jsonl', 'errors.jsonl'):
            raise ValueError('Unexpected file name in collection')
        raw = (root / name).read_bytes()
        if sha(raw) != checksum:
            raise ValueError('Response file hash mismatch')
        for line in raw.splitlines():
            record = json.loads(line)
            key = record.get('custom_id')
            if key not in keys or key in returned:
                raise ValueError('Unknown or repeated response ID')
            returned[key] = record
    rows = []
    usage, statuses, backends = {}, {}, {}
    for key, (case, mask, seed) in keys.items():
        state, reply, body = outcome(returned.get(key), P['model'])
        statuses.setdefault(case, Counter())[state] += 1
        usage.setdefault(case, Counter())
        fingerprint = body.get('system_fingerprint') or ''
        if state == 'completed':
            backends.setdefault(case, Counter())[fingerprint or '(unreported)'] += 1
        tokens = body.get('usage') or {}
        if all(isinstance(tokens.get(k), int) and tokens[k] >= 0 for k in ('prompt_tokens','completion_tokens')):
            usage[case].update({'reported_slots': 1, 'input': tokens['prompt_tokens'],
                                'output': tokens['completion_tokens'],
                                'cached_input': (tokens.get('prompt_tokens_details') or {}).get('cached_tokens', 0)})
        mapped = measure(reply, case) if state == 'completed' else dict.fromkeys(METRICS)
        rows.append({'case': case, 'mask': mask, 'seed': seed, 'active': mask.bit_count(),
                     'status': state, 'backend': fingerprint, 'reply': reply, **mapped})
    prices=PREVIOUS['batch_usd_per_million']
    cost={case:(tokens['input']*prices['input']+tokens['output']*prices['output'])/1_000_000
          for case,tokens in usage.items()}
    times={k:datetime.fromtimestamp(batch[k],timezone.utc).isoformat() for k in
           ('created_at','in_progress_at','finalizing_at','completed_at','expired_at','failed_at','cancelled_at')
           if isinstance(batch.get(k),int)}
    return rows, {'provider': batch['request_counts'], 'status': batch['status'],'times_utc':times,
                  'files_sha256': receipt['files'], 'requests_sha256': lock['input_jsonl_sha256'],
                  'statuses': statuses, 'usage': usage, 'backends': backends,
                  'listed_cost_usd_for_reported_usage_by_case':cost,
                  'listed_cost_usd_for_reported_usage':sum(cost.values())}


def main():
    original, added = {}, {}
    for mask in range(4096):
        for seed in SEEDS:
            base = design.slot_id(mask, seed)
            original[base] = ('uncertain', mask, seed)
            for case in P['cases']:
                added[case+'-'+base] = (case, mask, seed)
    lock = read(HERE / 'design-lock.json')
    if any(lock[k] != v for k,v in bindings().items()):
        raise ValueError('Frozen definitions differ')
    historical, old_receipt = consume(design.RUN, read(PARENT / 'design-lock.json'), original, historical=True)
    recent, new_receipt = consume(RUN, lock, added)
    all_rows = historical + recent
    # Keep the joined words private; the public measurement file has no free-form generated text.
    RESULTS.mkdir(exist_ok=True)
    private = RUN / 'replies.csv'
    private.touch(mode=0o600, exist_ok=True)
    save_csv(private, all_rows)
    save_csv(RESULTS / 'slot-features.csv', [{k:v for k,v in r.items() if k not in ('reply',)} for r in all_rows])
    receipts = {'historical': old_receipt, 'new': new_receipt}
    (RESULTS / 'coverage.json').write_text(json.dumps(receipts, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k:r['statuses'] for k,r in receipts.items()}, sort_keys=True))


if __name__ == '__main__':
    main()
