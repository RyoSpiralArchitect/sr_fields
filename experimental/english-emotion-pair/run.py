"""Prepare, submit once, or collect the two-prompt addition to the English powerset."""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'english-powerset'
RUN = HERE.parents[1] / '.runs' / HERE.name
sys.path.insert(0, str(PARENT))
import batch
import design
from design import packed, read, sha


def bindings():
    return {'features_sha256': sha((HERE / 'measures.py').read_bytes()),
            'protocol_sha256': sha((HERE / 'protocol.json').read_bytes()),
            'plan_sha256': sha((HERE / 'plan.md').read_bytes()),
            'parent_features_sha256': sha((PARENT / 'features.py').read_bytes()),
            'parent_protocol_sha256': sha((PARENT / 'protocol.json').read_bytes())}


def prepare():
    config = read(HERE / 'protocol.json')
    previous = read(PARENT / 'protocol.json')
    previous_lock = read(PARENT / 'design-lock.json')
    frozen = bindings()
    if (frozen['parent_features_sha256'] != previous_lock['features_sha256']
            or frozen['parent_protocol_sha256'] != previous_lock['protocol_sha256']
            or previous['model'] != config['model'] or previous['seeds'] != config['seeds']
            or previous['input'].count(config['replace_historical_text']) != 1):
        raise ValueError('The parent experiment differs from the frozen design')
    RUN.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = RUN / 'requests.jsonl'
    parent_hash, digest = hashlib.sha256(), hashlib.sha256()
    ids = set()
    input_size = 0
    with tempfile.NamedTemporaryFile(dir=RUN, delete=False) as handle:
        temp = Path(handle.name)
        try:
            for row in design.design():
                parent_hash.update(packed(row) + b'\n')
                key = row['custom_id']
                body = row['body']
                cases = sorted(config['cases'], key=lambda case: sha((config['pair_order_salt'] + key + case).encode()))
                for case in cases:
                    user = previous['input'].replace(config['replace_historical_text'], config['cases'][case])
                    new_key = case + '-' + key
                    if new_key in ids:
                        raise ValueError('Duplicate generation slot')
                    ids.add(new_key)
                    new_body = {**body, 'messages': [body['messages'][0], {'role': 'user', 'content': user}]}
                    line = packed({**row, 'custom_id': new_key, 'body': new_body}) + b'\n'
                    handle.write(line)
                    digest.update(line)
                    input_size += len(line)
            if (len(ids) != 24576 or config['expected_new_requests'] != len(ids) or input_size >= 200_000_000
                    or parent_hash.hexdigest() != previous_lock['input_jsonl_sha256']):
                raise ValueError('Requested inputs failed the frozen count, size or parent identity check')
            handle.flush()
            os.fsync(handle.fileno())
            if target.exists():
                if sha(target.read_bytes()) != digest.hexdigest():
                    raise ValueError('Existing input file differs')
            else:
                os.link(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    result = {**frozen, 'parent_requests_sha256': parent_hash.hexdigest(), 'requests': len(ids),
              'masks_per_prompt': 4096, 'input_jsonl_bytes': input_size, 'input_jsonl_sha256': digest.hexdigest()}
    lock = HERE / 'design-lock.json'
    if lock.exists():
        if read(lock) != result:
            raise ValueError('Existing design lock differs')
    else:
        design.write_once(lock, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'submit', 'status', 'collect'))
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps(prepare(), indent=2))
        return
    if args.action == 'submit':
        lock = read(HERE / 'design-lock.json')
        if any(lock.get(k) != v for k, v in bindings().items()):
            raise ValueError('Protocol or analysis definitions differ from the design lock')
        record = batch.submit(HERE, RUN, experiment=HERE.name, expected=24576, measure_file='measures.py')
    else:
        record = batch.status(RUN)
        if args.action == 'collect':
            batch.collect(record, RUN)
    print(json.dumps({k: record.get(k) for k in ('status', 'request_counts', 'errors', 'created_at', 'expires_at')}))


if __name__ == '__main__':
    main()
