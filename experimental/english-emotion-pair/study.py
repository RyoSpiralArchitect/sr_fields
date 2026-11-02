"""Matched Field and prompt differences, surface similarities and wording concentration."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import csv
import math
import statistics
import sys

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_texts import CASES, FIELDS, METRICS, OLD_METRICS, RESULTS, RUN, SEEDS
from analyze import save_csv
from features import words

COMPARISONS = [('embarrassed', 'happy'), ('uncertain', 'embarrassed'), ('uncertain', 'happy')]


def arrays(rows):
    shape = (4096, len(SEEDS), len(METRICS))
    values = {case: np.full(shape, np.nan) for case in CASES}
    texts = {case: {} for case in CASES}
    for row in rows:
        if row['status'] != 'completed':
            continue
        case, mask, seed = row['case'], int(row['mask']), int(row['seed'])
        values[case][mask, SEEDS.index(seed)] = [float(row[k]) if row[k] != '' else np.nan for k in METRICS]
        texts[case][mask,seed] = tuple(words(row['reply']))
    return values, texts


def estimates(label, diffs, measures=METRICS):
    rows = []
    for metric in measures:
        grouped = diffs[:,:,METRICS.index(metric)]
        finite = np.isfinite(grouped)
        totals = np.nansum(grouped, axis=0)
        counts = finite.sum(axis=0)
        n = int(counts.sum())
        scale = 1 if metric == 'words' else 100
        row = {**label, 'measure': metric, 'unit': 'words' if metric == 'words' else 'pp',
               'matched_blocks': n, 'delta': scale*float(totals.sum())/n if n else None}
        for s, total, count in zip(SEEDS, totals, counts):
            row[f'n_s{s}'] = int(count)
            row[f'delta_s{s}'] = scale*float(total)/int(count) if count else None
        rows.append(row)
    return rows


def factorial(values):
    masks = np.arange(4096)
    single, pairs, switches, stimuli = [], [], [], []
    for first, second in COMPARISONS:
        stimuli.extend(estimates({'from_case':first,'to_case':second}, values[second]-values[first]))
    for i, field in enumerate(FIELDS):
        bit = 1 << i
        off = masks[(masks & bit)==0]
        differences = {c: values[c][off|bit] - values[c][off] for c in CASES}
        for case in CASES:
            single.extend(estimates({'case':case,'field':field}, differences[case]))
        for first, second in COMPARISONS:
            switches.extend(estimates({'from_case':first,'to_case':second,'field':field},
                                      differences[second] - differences[first]))
    for i,j in combinations(range(len(FIELDS)),2):
        x,y = 1<<i,1<<j
        off = masks[(masks & (x|y))==0]
        for case, a in values.items():
            delta = a[off|x|y] - a[off|x] - a[off|y] + a[off]
            pairs.extend(estimates({'case':case,'first':FIELDS[i],'second':FIELDS[j]}, delta, OLD_METRICS))
    for name, data in [('field-effects',single),('field-pairs',pairs),
                       ('field-by-prompt',switches),('prompt-differences',stimuli)]:
        save_csv(RESULTS/(name+'.csv'), data)


def describe(values, texts):
    metric_rows, variety, phrases, similarities = [], [], [], []
    for case, by_slot in texts.items():
        counts = Counter(by_slot.values())
        n = sum(counts.values())
        if not n:
            raise ValueError(f'No eligible texts for {case}')
        entropy = -sum((v/n)*math.log2(v/n) for v in counts.values())
        variety.append({'case':case,'eligible':n,'unique_word_sequences':len(counts),
                        'top5_share':sum(v for _,v in counts.most_common(5))/n,
                        'entropy_bits':entropy,'effective_forms':2**entropy})
        for i, metric in enumerate(METRICS):
            a = values[case][:,:,i]
            available = np.isfinite(a)
            den = int(available.sum())
            metric_rows.append({'case':case,'measure':metric,'n':den,
                                'sum':int(np.nansum(a)) if den else None,
                                'mean':float(np.nansum(a))/den if den else None})
    for first, second in COMPARISONS:
        before, after = texts[first], texts[second]
        keys = before.keys() & after.keys()
        delta = Counter()
        support = Counter()
        dist, same = [], 0
        for key in sorted(keys):
            a,b = before[key], after[key]
            ba,bb = set(zip(a,a[1:])), set(zip(b,b[1:]))
            support.update(ba)
            support.update(bb)
            delta.update(bb-ba)
            delta.subtract(ba-bb)
            vocab_a, vocab_b = set(a),set(b)
            union = vocab_a|vocab_b
            dist.append(len(vocab_a&vocab_b)/len(union) if union else 1)
            same += a==b
        n = len(keys)
        similarities.append({'from_case':first,'to_case':second,'matched_slots':n,'same_word_sequences':same,
                             'mean_word_set_jaccard':statistics.fmean(dist) if dist else None})
        for direction in (1,-1):
            candidates = sorted((t for t,v in delta.items() if v*direction>0 and support[t]>=30),
                                key=lambda t:(-direction*delta[t],t))
            for bigram in candidates[:12]:
                phrases.append({'from_case':first,'to_case':second,'direction':'higher' if direction==1 else 'lower',
                                'bigram':' '.join(bigram),'support':support[bigram],
                                'matched_slots':n,'delta_pp':100*delta[bigram]/n})
    for name, entries in [('rates',metric_rows),('wording-diversity',variety),
                          ('paired-phrases',phrases),('text-similarity',similarities)]:
        save_csv(RESULTS/(name+'.csv'),entries)


def main():
    with (RUN/'replies.csv').open(newline='') as f:
        values,texts = arrays(csv.DictReader(f))
    factorial(values)
    describe(values,texts)
    print('Measured three prompts, twelve Field differences and 66 Field interactions per prompt.')


if __name__ == '__main__':
    main()
