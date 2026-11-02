"""Independently recompute the contrasts from the shareable per-slot measurements (no API)."""
import csv
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path
import sqlite3

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'


def table(name):
    with (RESULTS / (name + '.csv')).open(newline='') as handle:
        return list(csv.DictReader(handle))


def check(value, message):
    if not value:
        raise ValueError(message)


def agrees(actual, serialized):
    return actual is None and serialized == '' or (
        actual is not None and serialized != '' and math.isclose(actual, float(serialized), rel_tol=1e-10, abs_tol=1e-10))


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    summary = json.loads((RESULTS / 'summary.json').read_text())
    fields, seeds = protocol['fields_in_bit_order'], protocol['seeds']
    measures = protocol['primary_metrics'] + protocol['secondary_metrics']
    slots = table('slot-features')
    check(len(slots) == summary['expected'] == 4096*3, 'Unexpected row count')
    check({(int(r['mask']), int(r['seed'])) for r in slots} ==
          {(mask, seed) for mask in range(4096) for seed in seeds}, 'Missing or duplicate slot')
    check(dict(Counter(r['status'] for r in slots)) == summary['statuses'], 'Status count mismatch')
    for r in slots:
        check(int(r['active']) == int(r['mask']).bit_count(), 'Field count mismatch')
        for metric in measures:
            if r['status'] != 'completed':
                check(r[metric] == '', 'An excluded value leaked into the measurements')
            elif metric != 'words':
                check(r[metric] in ('0', '1'), 'Indicator is not binary')
            else:
                check(int(r[metric]) >= 0, 'Negative word count')

    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE replies(mask INTEGER, seed INTEGER, ' + ','.join(measures) + ')')
    db.executemany('INSERT INTO replies VALUES (' + ','.join('?' for _ in range(2 + len(measures))) + ')',
                   ((int(r['mask']), int(r['seed']), *(int(r[k]) for k in measures))
                    for r in slots if r['status'] == 'completed'))
    singles, pairs = table('field-contrasts'), table('pair-interactions')
    records = {((r['field'],), r['measure']): r for r in singles}
    records.update({((r['first'], r['second']), r['measure']): r for r in pairs})
    check(len(records) == len(singles) + len(pairs) == 78 * len(measures), 'Unexpected contrasts')
    names = [(name,) for name in fields] + list(combinations(fields, 2))
    for selected in names:
        mask = sum(1 << fields.index(f) for f in selected)
        # Group by the other bits. Only complete 2- or 4-cell blocks enter the means.
        positive = (mask,) if len(selected) == 1 else (0, mask)
        sign = '(CASE WHEN (mask & ?) IN (' + ','.join(str(n) for n in positive) + ') THEN 1 ELSE -1 END)'
        sums = ','.join(f'SUM({m}*{sign}) AS d_{m}' for m in measures)
        query = (f'SELECT seed, COUNT(*), ' + ','.join(f'SUM(d_{m})' for m in measures) +
                 f' FROM (SELECT seed,{sums} FROM replies GROUP BY seed,(mask & ~?) HAVING COUNT(*)=?) GROUP BY seed')
        totals = {r[0]: r[1:] for r in db.execute(query, [mask]*len(measures) + [mask, 2**len(selected)])}
        for i, metric in enumerate(measures, start=1):
            r = records[selected, metric]
            total = 0
            n = 0
            scale = 1 if metric == 'words' else 100
            for s in seeds:
                counts = totals.get(s, (0,) * (len(measures) + 1))
                check(counts[0] == int(r[f'n_s{s}']), 'Block count mismatch')
                avg = counts[i] * scale / counts[0] if counts[0] else None
                check(agrees(avg, r[f'delta_s{s}']), f'Seed-specific contrast mismatch: {selected}, {metric}, {s}')
                total += counts[i]
                n += counts[0]
            check(agrees(total*scale/n if n else None, r['delta']) and n == int(r['matched_sets']),
                  f'Pooled contrast mismatch: {selected}, {metric}')
    db.close()
    print(f'Checked {len(slots):,} expected mask/seed slots and {len(records):,} pooled contrasts, each at all three seeds.')


if __name__ == '__main__':
    main()
