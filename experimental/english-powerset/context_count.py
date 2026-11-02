"""Exploratory: does the ON-minus-OFF difference vary with the number of other active Fields?"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'


def main():
    p = json.loads((HERE / 'protocol.json').read_text())
    measures = p['primary_metrics'] + p['secondary_metrics']
    with (RESULTS / 'slot-features.csv').open(newline='') as f:
        table = {(int(r['mask']), int(r['seed'])): [int(r[k]) for k in measures]
                 for r in csv.DictReader(f) if r['status'] == 'completed'}
    rows = []
    for i, field in enumerate(p['fields_in_bit_order']):
        bit = 1 << i
        counts = [0]*12
        sums = [[0]*len(measures) for _ in counts]
        for (mask, seed), off in table.items():
            if mask & bit or (mask | bit, seed) not in table:
                continue
            on = table[mask | bit, seed]
            k = mask.bit_count()
            counts[k] += 1
            for j in range(len(measures)):
                sums[k][j] += on[j] - off[j]
        for k, n in enumerate(counts):
            rows.append({'field': field, 'other_active': k, 'matched_pairs': n,
                         **{metric: (sums[k][j] * (1 if metric == 'words' else 100) / n if n else None)
                            for j, metric in enumerate(measures)}})
    with (RESULTS / 'context-count.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
