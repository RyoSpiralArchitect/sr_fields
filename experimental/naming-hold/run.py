"""Preview or run the fixed, two-condition Japanese dialogue experiment."""
import argparse
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from field_observatory.prompts import digest, encoded
from field_observatory.provider import Session, private_write, request_body, transport


def prepare():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    conditions = protocol['conditions']
    if [slot['name'] for slot in conditions] != ['common', 'threshold']:
        raise ValueError('This protocol requires exactly the common and threshold slots, in order.')
    previews = []
    for slot in conditions:
        body, prompt = request_body(
            protocol['input'], 'custom', slot['mode'], protocol['model'],
            protocol['max_output_tokens'], language=protocol['language'], field_ids=slot['fields'],
        )
        if digest(encoded(body)) != slot['request_sha256']:
            raise ValueError(f"The request for {slot['name']} has changed. Review the protocol before execution.")
        previews.append({'condition': slot['name'], 'request': body, 'prompt': prompt})
    return protocol, previews


def execute(protocol, previews, directory, send=transport):
    if not os.environ.get('OPENAI_API_KEY'):
        raise ValueError('Set OPENAI_API_KEY in the local process environment.')
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    private_write(directory / 'plan.json', previews)

    conditions = protocol['conditions']
    expected = iter(slot['request_sha256'] for slot in conditions)

    def checked_send(body, key):
        if digest(encoded(body)) != next(expected):
            return {'status': 'protocol_changed', 'reply': ''}
        return send(body, key)

    session = Session(enabled=True, limit=2, model=protocol['model'],
                      output_tokens=protocol['max_output_tokens'], records=directory / 'records',
                      send=checked_send)
    slots = []
    for slot in conditions:
        if session.stopped:
            slots.append({'condition': slot['name'], 'status': 'not_attempted'})
            continue
        result = session.run(protocol['input'], 'custom', slot['mode'],
                             language=protocol['language'], field_ids=slot['fields'])
        slots.append({'condition': slot['name'], 'status': result['status'], 'run_id': result['run_id']})
    private_write(directory / 'slots.json', slots)
    return slots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Send up to two OpenAI requests')
    args = parser.parse_args()
    protocol, previews = prepare()
    if not args.execute:
        print(json.dumps(previews, ensure_ascii=False, indent=2))
        return 0
    try:
        slots = execute(protocol, previews, ROOT / '.runs' / 'naming-hold')
    except FileExistsError:
        parser.exit(1, 'This checkout already has a naming-hold run. Inspect its records before any new trial.\n')
    print(json.dumps(slots, ensure_ascii=False, indent=2))
    return 0 if all(slot['status'] == 'completed' for slot in slots) else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
