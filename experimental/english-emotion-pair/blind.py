"""Draw the prespecified reading sample and reveal field conditions only after the labels are locked."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
RUN = HERE.parents[1] / '.runs' / HERE.name
CASES = ('uncertain', 'embarrassed', 'happy')
CODES = {'OPEN', 'OFFER', 'ASSUME', 'UNCLEAR'}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def positions():
    p = json.loads((HERE / 'protocol.json').read_text())
    salt = p['sample_salt']
    sample = []
    for seed in p['seeds']:
        masks = sorted(range(4096), key=lambda m: digest(f'{salt}|mask|{seed}|{m}'))[:p['sample_per_seed']]
        for mask in masks:
            for case in CASES:
                key = digest(f'{salt}|blinded|{case}|{mask}|{seed}')[:16]
                sample.append((key, case, mask, seed))
    return sorted(sample)


def prepare():
    import run
    with (RUN / 'replies.csv').open(newline='') as f:
        rows = {(r['case'], int(r['mask']), int(r['seed'])):r for r in csv.DictReader(f)}
    path = RUN / 'blind-lines.jsonl'
    items = []
    for i, (_, case, mask, seed) in enumerate(positions(), 1):
        r = rows[case, mask, seed]
        items.append({'id': i, 'stimulus': case, 'reply': r['reply'], 'status': r['status']})
    encoded = ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in items)
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Existing blinded sample differs')
    path.write_text(encoded)
    path.chmod(0o600)
    sample_receipt={'blind_lines_sha256':digest(encoded),'selection_sha256':digest(json.dumps(positions())),
                    'slots':len(items)}
    receipt=RUN/'blind-sample-lock.json'
    if receipt.exists():
        if run.read(receipt)!=sample_receipt:
            raise ValueError('Blinded sample receipt differs')
    else:
        run.design.write_once(receipt,sample_receipt)
    print('Prepared', len(items), 'blinded reading slots')


def reveal():
    import run
    encoded=(RUN / 'blind-lines.jsonl').read_text()
    receipt=run.read(RUN/'blind-sample-lock.json')
    if receipt['blind_lines_sha256']!=digest(encoded) or receipt['selection_sha256']!=digest(json.dumps(positions())):
        raise ValueError('Reading sample changed before the labels were locked')
    sample = [json.loads(line) for line in encoded.splitlines()]
    source = RUN / 'blind-labels.csv'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open(newline='') as file:
        labels = list(csv.DictReader(file))
    if [int(r['id']) for r in labels] != list(range(1, len(sample)+1)) or len(sample) != 144:
        raise ValueError('Labels must cover all sampled slots in their original blind order')
    for row, rec in zip(labels, sample):
        if row['code'] not in (CODES if rec['status'] == 'completed' else {'MISSING'}) or not row['note'].strip():
            raise ValueError('Invalid label or unavailable response')
    lock_path = RUN / 'blind-label-lock.json'
    if lock_path.exists():
        if run.read(lock_path)['sha256'] != checksum:
            raise ValueError('The original labels have changed')
    else:
        run.design.write_once(lock_path, {'sha256': checksum,'blind_lines_sha256':digest(encoded)})
    dest = HERE / 'results' / 'reading.csv'
    with dest.open('w', newline='') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(['blind_id','case','mask','seed','code','note'])
        for label, (_, case, mask, seed) in zip(labels, positions()):
            writer.writerow([label['id'], case, mask, seed, label['code'], label['note']])
    print('Locked original labels and exported', len(labels), 'coded slots')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'reveal'))
    if parser.parse_args().action == 'prepare':
        prepare()
    else:
        reveal()
