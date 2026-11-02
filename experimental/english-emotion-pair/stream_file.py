"""Single-file transfer with bounded writes. This command never starts a generation."""
import json
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import HERE, RUN, batch, bindings, design, read, sha


def record_verified_file(file):
    lock = read(HERE/'design-lock.json')
    if file['bytes'] != lock['input_jsonl_bytes'] or file['purpose'] != 'batch':
        raise ValueError('Provider input size or purpose differs')
    raw = batch.api('GET','files/'+batch.resource_id(file['id'])+'/content',limit=120_000_000,timeout=300)
    if sha(raw) != lock['input_jsonl_sha256']:
        raise ValueError('Downloaded provider input differs')
    design.write_once(RUN/'verified-file.json',{'file':file,'sha256':sha(raw),'bytes':len(raw)})
    design.write_once(RUN/'upload.json',file)


def main():
    lock = read(HERE/'design-lock.json')
    data = (RUN/'requests.jsonl').read_bytes()
    key = os.environ.get('OPENAI_API_KEY')
    if not key or key.encode() in data or len(data)!=lock['input_jsonl_bytes'] or sha(data)!=lock['input_jsonl_sha256']:
        raise ValueError('Input preflight failed')
    if any(lock[k] != v for k,v in bindings().items()) or (RUN/'create-attempt.json').exists() or (RUN/'upload.json').exists():
        raise ValueError('Unresolved design or generation state')
    short = HERE.name+'-'+lock['input_jsonl_sha256'][:12]
    filename = short+'-stream.jsonl'
    page = json.loads(batch.api('GET','files?purpose=batch&order=desc&limit=100'))
    found = [f for f in page['data'] if f['filename'] in (short+'.jsonl',filename) and f['bytes']==len(data)]
    if found:
        record_verified_file(found[0])
        print('Reconciled an existing complete input file.')
        return
    marker=RUN/'stream-attempt.json'
    design.write_once(marker,{'at':int(time.time()),'bytes':len(data),'sha256':sha(data),'matching_files_at_start':0})
    boundary='observatory'+uuid.uuid4().hex
    head=(f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
          f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
          'Content-Type: application/jsonl\r\n\r\n').encode()
    tail=f'\r\n--{boundary}--\r\n'.encode()
    def pieces():
        yield head
        size=512*1024
        for start in range(0,len(data),size):
            yield memoryview(data)[start:start+size]
            if (start+size)%(16*1024*1024)==0:
                print('Sent', (start+size)//(1024*1024), 'MiB',flush=True)
        yield tail
    body=batch.api('POST','files',pieces(),'multipart/form-data; boundary='+boundary,
                   timeout=300,content_length=len(head)+len(data)+len(tail))
    file=json.loads(body)
    design.write_once(RUN/'stream-file-receipt.json',file)
    if file['filename']!=filename: raise ValueError('Unexpected remote filename')
    record_verified_file(file)
    print('Verified the remote bytes of the streamed input file.')


if __name__=='__main__':
    main()
