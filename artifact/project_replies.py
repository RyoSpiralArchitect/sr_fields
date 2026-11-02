"""Project only the recorded reply strings and their positions from the two frozen studies."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STUDY = ROOT / 'experimental/english-emotion-pair'
PARENT = ROOT / 'experimental/english-powerset'
CASES = ['uncertain', 'embarrassed', 'happy']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def main():
    coverage = json.loads((STUDY / 'results/coverage.json').read_bytes())
    protocol = json.loads((PARENT / 'protocol.json').read_bytes())
    seeds, fields = protocol['seeds'], protocol['fields_in_bit_order']
    replies = {}
    for name, source in [('historical', PARENT), ('new', STUDY)]:
        raw = (ROOT / '.runs' / source.name / 'output.jsonl').read_bytes()
        if sha(raw) != coverage[name]['files_sha256']['output.jsonl']:
            raise ValueError('Unexpected raw response file')
        for line in raw.splitlines():
            envelope = json.loads(line)
            key = envelope['custom_id']
            case, key = ('uncertain', key) if name == 'historical' else key.split('-', 1)
            match = re.fullmatch(r'm([0-9a-f]{3})-s(101|202|303)', key)
            if not match or case not in (CASES[:1] if name == 'historical' else CASES[1:]):
                raise ValueError('Unexpected response slot')
            slot = (int(match[1], 16), int(match[2]), case)
            response = envelope['response']
            body = response['body']
            choice, = body['choices']
            text = choice['message']['content']
            if (slot in replies or envelope.get('error') or response['status_code'] != 200 or
                    body['model'] != protocol['model'] or choice['finish_reason'] != 'stop' or
                    choice['message'].get('refusal') or not isinstance(text, str) or
                    not re.fullmatch(r"""[A-Za-z .,?!'’‘“”";:—–-]{1,512}""", text)):
                raise ValueError(f'Unreviewed or duplicate response at {slot}')
            replies[slot] = text
    if len(replies) != 36_864 or len(fields) != 12:
        raise ValueError('Incomplete release projection')
    forms = sorted(set(replies.values()))
    indices = {v: i for i, v in enumerate(forms)}
    slots = [[indices[replies[mask, seed, case]] for seed in seeds for case in CASES] for mask in range(4096)]
    # One string or mask per line also makes the release projection reviewable in Git.
    text = ('{\n"cases":' + compact(CASES) + ',\n"seeds":' + compact(seeds) +
            ',\n"fields":' + compact(fields) + ',\n"forms":[\n' + ',\n'.join(map(compact, forms)) +
            '\n],\n"slots":[\n' + ',\n'.join(map(compact, slots)) + '\n]\n}\n')
    encoded = text.encode()
    receipt = {'slots': len(replies), 'verbatim_forms': len(forms), 'projection_sha256': sha(encoded),
               'source_output_sha256': {name: coverage[name]['files_sha256']['output.jsonl'] for name in coverage}}
    for path, data in [(HERE/'replies.json', encoded),
                       (HERE/'projection-receipt.json', (json.dumps(receipt, indent=2)+'\n').encode())]:
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f'Existing release projection differs: {path.name}')
        if not path.exists():
            path.write_bytes(data)
    print(f'Projected {len(replies):,} slots into {len(forms):,} exact strings. SHA-256 {sha(encoded)}')


if __name__ == '__main__':
    main()
