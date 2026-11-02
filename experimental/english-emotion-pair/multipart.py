"""Upload the frozen bytes in small parts, without starting any model requests."""
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import HERE, RUN, batch, bindings, design, packed, read, sha


def main():
    lock = read(HERE / 'design-lock.json')
    data = (RUN / 'requests.jsonl').read_bytes()
    if (any(lock[k] != v for k,v in bindings().items()) or sha(data) != lock['input_jsonl_sha256']
            or len(data) != lock['input_jsonl_bytes'] or data.count(b'\n') != 24576):
        raise ValueError('Frozen inputs differ')
    key = os.environ.get('OPENAI_API_KEY')
    if not key or key.encode() in data:
        raise ValueError('Credential preflight failed')
    if (RUN/'upload.json').exists() or (RUN/'create-attempt.json').exists():
        raise ValueError('Input file or batch creation already recorded')
    if (RUN/'upload-attempt.json').exists():
        first = read(RUN/'upload-reconciliation-first.json')
        if first.get('matches') != 0 or first.get('batch_create_attempted') is not False:
            raise ValueError('Reconcile the first file upload before continuing')
    path = RUN/'multipart'
    path.mkdir(mode=0o700, exist_ok=True)
    filename = HERE.name + '-' + lock['input_jsonl_sha256'][:12] + '.jsonl'
    if not (path/'upload.json').exists():
        design.write_once(path/'create-attempt.json', {'input_sha256':sha(data)})
        record = json.loads(batch.api('POST','uploads',packed({'purpose':'batch','filename':filename,
                                 'bytes':len(data),'mime_type':'application/jsonl'})))
        design.write_once(path/'upload.json', record)
    upload_id = batch.resource_id(read(path/'upload.json')['id'])
    base = 'uploads/'+upload_id
    part_ids = []
    block = 8 * 1024 * 1024
    for i,start in enumerate(range(0,len(data),block)):
        chunk = data[start:start+block]
        receipt = path/f'part-{i:02}.json'
        if not receipt.exists():
            design.write_once(path/f'attempt-{i:02}.json',{'start':start,'bytes':len(chunk),'sha256':sha(chunk)})
            boundary = 'observatory'+uuid.uuid4().hex
            start_bytes = (f'--{boundary}\r\nContent-Disposition: form-data; name="data"; filename="part"\r\n'
                           'Content-Type: application/octet-stream\r\n\r\n').encode()
            content = start_bytes + chunk + f'\r\n--{boundary}--\r\n'.encode()
            part = json.loads(batch.api('POST',base+'/parts',content,'multipart/form-data; boundary='+boundary,timeout=180))
            if part.get('upload_id') != upload_id:
                raise ValueError('Unexpected part owner')
            design.write_once(receipt,part)
        part_ids.append(batch.resource_id(read(receipt)['id']))
        print(f'Part {i+1} recorded',flush=True)
    design.write_once(path/'complete-attempt.json',{'parts':len(part_ids),'input_sha256':sha(data)})
    complete = json.loads(batch.api('POST',base+'/complete',packed({'part_ids':part_ids,
                                 'md5':hashlib.md5(data,usedforsecurity=False).hexdigest()}),timeout=180))
    design.write_once(path/'complete.json',complete)
    file = complete['file']
    if complete['status'] != 'completed' or file['bytes'] != len(data) or file['filename'] != filename:
        raise ValueError('Completed upload has different properties')
    design.write_once(RUN/'upload.json',file)
    print('Complete input file recorded. No generation was submitted.')


if __name__ == '__main__':
    main()
