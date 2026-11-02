"""Submit the frozen sweep once; status and collection perform only reads at the provider."""
import argparse
import http.client
import json
import os
import re
import ssl
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from design import HERE, RUN, packed, read, sha, write_once

TERMINAL = {'completed', 'expired', 'cancelled', 'failed'}


def api(method, path, body=None, content_type='application/json', limit=4_000_000, timeout=120):
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise ValueError('OPENAI_API_KEY is missing')
    conn = http.client.HTTPSConnection('api.openai.com', timeout=timeout, context=ssl.create_default_context())
    try:
        conn.request(method, '/v1/' + path, body, {'Authorization': 'Bearer ' + key, 'Content-Type': content_type})
        res = conn.getresponse()
        if res.status != 200 and res.status != 201:
            raw = res.read(8192)
            try:
                error = json.loads(raw)['error']
                detail = str(error.get('message', ''))[:400].replace(key, '[redacted]')
            except (ValueError, KeyError, TypeError):
                detail = 'No structured provider message'
            raise RuntimeError(f'Provider HTTP {res.status}: {detail}')
        data = res.read(limit + 1)
        if len(data) > limit or key.encode() in data:
            raise ValueError('Response size or credential guard rejected the result')
        return data
    finally:
        conn.close()


def resource_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', value):
        raise ValueError('Invalid provider resource identifier')
    return value


def submit():
    lock = read(HERE / 'design-lock.json')
    data = (RUN / 'requests.jsonl').read_bytes()
    if (sha(data) != lock['input_jsonl_sha256'] or data.count(b'\n') != lock['requests']
            or lock['requests'] != 12288 or len(data) != lock['input_jsonl_bytes']
            or sha((HERE / 'features.py').read_bytes()) != lock['features_sha256']
            or sha((HERE / 'protocol.json').read_bytes()) != lock['protocol_sha256']):
        raise ValueError('Frozen input or analysis specification differs')
    key = os.environ.get('OPENAI_API_KEY')
    if not key or key.encode() in data:
        raise ValueError('Credential preflight failed')
    # Both markers are exclusive. An ambiguous POST is never replayed.
    if not (RUN / 'upload.json').exists():
        write_once(RUN / 'upload-attempt.json', {'sha256': sha(data)})
        boundary = 'observatory' + uuid.uuid4().hex
        start = (f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
                 f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="english-powerset-{sha(data)[:12]}.jsonl"\r\n'
                 'Content-Type: application/jsonl\r\n\r\n').encode()
        payload = start + data + f'\r\n--{boundary}--\r\n'.encode()
        upload = json.loads(api('POST', 'files', payload, 'multipart/form-data; boundary=' + boundary))
        if upload.get('bytes') != len(data):
            raise ValueError('Uploaded size mismatch')
        write_once(RUN / 'upload.json', upload)
    file_id = resource_id(read(RUN / 'upload.json')['id'])
    job = {'input_file_id': file_id, 'endpoint': '/v1/chat/completions', 'completion_window': '24h',
           'metadata': {'experiment': 'english-powerset', 'design_sha256': lock['input_jsonl_sha256']}}
    write_once(RUN / 'create-attempt.json', job)
    batch = json.loads(api('POST', 'batches', packed(job)))
    resource_id(batch['id'])
    write_once(RUN / 'batch.json', batch)
    return batch


def status():
    job = read(RUN / 'batch.json')
    value = json.loads(api('GET', 'batches/' + resource_id(job['id'])))
    if value['id'] != job['id'] or value['input_file_id'] != read(RUN / 'upload.json')['id']:
        raise ValueError('Receipt identifies a different batch')
    return value


def collect(batch):
    if batch['status'] not in TERMINAL:
        raise ValueError('The batch is still processing')
    # Save each completed download atomically so a partial response cannot be mistaken for a result.
    file_hashes = {}
    for field, name in [('output_file_id', 'output.jsonl'), ('error_file_id', 'errors.jsonl')]:
        fid = batch.get(field)
        if not fid:
            continue
        path = RUN / name
        if not path.exists():
            raw = api('GET', 'files/' + resource_id(fid) + '/content', limit=250_000_000)
            temp = RUN / ('.' + name + '-' + uuid.uuid4().hex)
            try:
                with os.fdopen(os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as handle:
                    handle.write(raw)
                os.link(temp, path)
            finally:
                temp.unlink(missing_ok=True)
        file_hashes[name] = sha(path.read_bytes())
    receipt = {'batch': batch, 'files': file_hashes}
    path = RUN / 'collection.json'
    if not path.exists():
        write_once(path, receipt)
    elif read(path)['files'] != file_hashes:
        raise ValueError('Collected files no longer match the receipt')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('submit', 'status', 'collect'))
    args = parser.parse_args()
    batch = submit() if args.action == 'submit' else status()
    if args.action == 'collect':
        collect(batch)
    print(json.dumps({k: batch.get(k) for k in ('status', 'request_counts', 'errors', 'created_at', 'expires_at')}))


if __name__ == '__main__':
    main()
