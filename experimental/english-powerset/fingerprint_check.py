"""Post hoc sensitivity: paired differences when the recorded provider fingerprints also match."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
RUN = HERE.parents[1] / '.runs' / 'english-powerset'


def main():
    p = json.loads((HERE / 'protocol.json').read_text())
    metrics = p['primary_metrics'] + p['secondary_metrics']
    with (RESULTS / 'slot-features.csv').open(newline='') as f:
        rows = {(int(r['mask']), int(r['seed'])): r for r in csv.DictReader(f) if r['status'] == 'completed'}
    key_for = {f'm{m:03x}-s{s}': (m,s) for m,s in rows}
    fps = {}
    with (RUN / 'output.jsonl').open() as stream:
        for line in stream:
            result = json.loads(line)
            key = key_for.get(result['custom_id'])
            if key is not None:
                fingerprint = result['response']['body'].get('system_fingerprint')
                if fingerprint:
                    fps[key] = fingerprint
    output = []
    for i, field in enumerate(p['fields_in_bit_order']):
        bit = 1 << i
        pairs = [((m, s),(m | bit, s)) for m,s in fps if not m & bit and fps[m,s] == fps.get((m | bit,s))]
        n = len(pairs)
        output.append({'field': field, 'matched_pairs': n,
                       **{k: (sum(int(rows[b][k])-int(rows[a][k]) for a,b in pairs) *
                              (1 if k == 'words' else 100) / n if n else None) for k in metrics}})
    with (RESULTS / 'fingerprint-matched.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(output)


if __name__ == '__main__':
    main()
