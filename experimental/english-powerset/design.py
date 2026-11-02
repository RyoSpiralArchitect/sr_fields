"""Generate one frozen request per (mask, seed). This command is entirely offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / '.runs' / 'english-powerset'
sys.path.insert(0, str(ROOT / 'runtime'))
from field_observatory.prompts import catalog, compile_prompt


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packed(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path):
    return json.loads(path.read_bytes())


def write_once(path, obj):
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
        f.flush()
        os.fsync(f.fileno())


def slot_id(mask, seed):
    return f'm{mask:03x}-s{seed}'


def design():
    p = read(HERE / 'protocol.json')
    fields = p['fields_in_bit_order']
    actual = [f['id'] for f in catalog()[0]['fields']]
    if len(fields) != 12 or fields != actual or len(set(p['seeds'])) != 3 or len(p['seeds']) != 3:
        raise ValueError('The fixed design requires the catalog order and three distinct seeds')
    instructions = []
    for mask in range(1 << len(fields)):
        selected = [name for i, name in enumerate(fields) if mask & (1 << i)]
        item = compile_prompt('custom', 'structured' if mask else 'baseline', language='en', field_ids=selected)
        instructions.append(item['instructions'])
    if len(set(instructions)) != 4096:
        raise ValueError('Expected 4,096 distinct compiled prompts')
    pairs = [(m, s) for m in range(len(instructions)) for s in p['seeds']]
    pairs.sort(key=lambda v: sha((p['submission_order_salt'] + slot_id(*v)).encode()))
    for mask, seed in pairs:
        body = {'model': p['model'], 'seed': seed, 'temperature': p['temperature'], 'top_p': p['top_p'],
                'max_completion_tokens': p['max_completion_tokens'], 'n': 1, 'store': False,
                'messages': [{'role': 'system', 'content': instructions[mask]}, {'role': 'user', 'content': p['input']}]}
        yield {'method': 'POST', 'url': p['endpoint'], 'custom_id': slot_id(mask, seed), 'body': body}


def prepare():
    RUN.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = RUN / 'requests.jsonl'
    digest = hashlib.sha256()
    seen = set()
    message_bytes = total = 0
    with tempfile.NamedTemporaryFile(dir=RUN, delete=False) as f:
        temp = Path(f.name)
        try:
            for row in design():
                if row['custom_id'] in seen:
                    raise ValueError('Duplicate slot')
                seen.add(row['custom_id'])
                line = packed(row) + b'\n'
                f.write(line)
                digest.update(line)
                total += len(line)
                message_bytes += sum(len(m['content'].encode()) for m in row['body']['messages'])
            if len(seen) != 12288 or total > 200_000_000:
                raise ValueError('Request count or file size violates the frozen budget')
            f.flush()
            os.fsync(f.fileno())
            if target.exists():
                if sha(target.read_bytes()) != digest.hexdigest():
                    raise ValueError('Existing request file differs; refusing replacement')
            else:
                os.link(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    return {'requests': len(seen), 'combinations': 4096, 'input_jsonl_bytes': total,
            'message_utf8_bytes': message_bytes, 'input_jsonl_sha256': digest.hexdigest(),
            'protocol_sha256': sha((HERE / 'protocol.json').read_bytes()),
            'features_sha256': sha((HERE / 'features.py').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', required=True, action='store_true')
    parser.parse_args()
    print(json.dumps(prepare(), indent=2))
