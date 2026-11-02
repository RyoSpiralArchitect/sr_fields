"""Build a private, offline reader for the completed run. No credentials or API access."""
import csv
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1] / '.runs' / 'english-powerset'


def main():
    p = json.loads((HERE / 'protocol.json').read_text())
    with (RUN / 'eligible-replies.csv').open(newline='') as f:
        text = {(int(r['mask']), int(r['seed'])): r['reply'] for r in csv.DictReader(f)}
    with (HERE / 'results' / 'slot-features.csv').open(newline='') as f:
        states = {(int(r['mask']), int(r['seed'])): r['status'] for r in csv.DictReader(f)}
    with (HERE / 'results' / 'field-contrasts.csv').open(newline='') as f:
        effects = {name: {} for name in p['fields_in_bit_order']}
        for row in csv.DictReader(f):
            if row['measure'] in p['primary_metrics']:
                effects[row['field']][row['measure']] = [float(row['delta']) if row['delta'] else None,
                                                         int(row['matched_sets'])]
    payload = {'fields': p['fields_in_bit_order'], 'seeds': p['seeds'], 'input': p['input'],
               'effects': effects, 'lines': [[text.get((m, s), '[' + states[m, s] + ']') for s in p['seeds']]
                                            for m in range(4096)]}
    # Escape the data block, including closing script tags in arbitrary generated text.
    encoded = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).replace('<', r'\u003c').replace('&', r'\u0026')
    template = (HERE / 'reader.html').read_text()
    if template.count('%%LOCAL_DATA%%') != 1:
        raise ValueError('Missing unique data slot')
    path = RUN / 'compare-replies.html'
    with os.fdopen(os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), 'w', encoding='utf-8') as f:
        f.write(template.replace('%%LOCAL_DATA%%', encoded))
    print(f'Offline reader: {len(text):,} replies, {len(payload["lines"]):,} combinations.')


if __name__ == '__main__':
    main()
