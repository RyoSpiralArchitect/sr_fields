"""Verify the public evidence and build the offline research reader without private inputs."""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'artifact'
PARENT = ROOT / 'experimental/english-powerset'
STUDY = ROOT / 'experimental/english-emotion-pair'
sys.path[:0] = [str(STUDY), str(PARENT)]
from measures import measure


def sha(data):
    return hashlib.sha256(data).hexdigest()


def table(name):
    with (STUDY/'results'/name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def public_payload():
    raw = (SRC/'replies.json').read_bytes()
    release = json.loads((SRC/'projection-receipt.json').read_bytes())
    coverage = json.loads((STUDY/'results/coverage.json').read_bytes())
    if (sha(raw) != release['projection_sha256'] or
            {k:v['files_sha256']['output.jsonl'] for k,v in coverage.items()} != release['source_output_sha256']):
        raise ValueError('Projection provenance differs')
    data = json.loads(raw)
    parent = json.loads((PARENT/'protocol.json').read_bytes())
    protocol = json.loads((STUDY/'protocol.json').read_bytes())
    cases, seeds, fields = data['cases'], data['seeds'], data['fields']
    forms, slots = data['forms'], data['slots']
    if (set(data) != {'cases','seeds','fields','forms','slots'} or cases != ['uncertain','embarrassed','happy']
            or seeds != parent['seeds'] or fields != parent['fields_in_bit_order'] or
            forms != sorted(set(forms)) or len(forms) != release['verbatim_forms'] or len(slots) != 4096 or
            any(len(row) != 9 or any(type(v) is not int or not 0 <= v < len(forms) for v in row) for row in slots)):
        raise ValueError('Invalid public reply index')
    seen = set()
    cache = {}
    for row in table('slot-features.csv'):
        case, mask, seed = row['case'], int(row['mask']), int(row['seed'])
        key = (case, mask, seed)
        if key in seen or not 0 <= mask < 4096 or row['status'] != 'completed':
            raise ValueError('Unexpected measurement slot')
        seen.add(key)
        form = slots[mask][seeds.index(seed)*len(cases) + cases.index(case)]
        if (case, form) not in cache:
            cache[case, form] = measure(forms[form], case)
        if any(row[k] != ('' if v is None else str(v)) for k,v in cache[case, form].items()):
            raise ValueError(f'Published wording does not reproduce its measurements at {key}')
    if len(seen) != release['slots'] or len(seen) != 36_864:
        raise ValueError('Public measurements have incomplete coverage')
    data['cues'] = {'uncertain': protocol['replace_historical_text'], **protocol['cases']}
    data['dialogue'] = parent['input']
    data['rates'] = {row['case']: {'hits': int(row['sum']), 'n': int(row['n'])}
                     for row in table('rates.csv') if row['measure'] == 'question'}
    measures = ('question','invitation','echo_exact')
    data['effects'] = {field: {metric: {} for metric in measures} for field in fields}
    for row in table('field-effects.csv'):
        if row['measure'] in measures:
            data['effects'][row['field']][row['measure']][row['case']] = float(row['delta']) if row['delta'] else None
    return data, release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'build/public-artifact')
    args = parser.parse_args()
    data, release = public_payload()
    template = (SRC/'reader.html').read_text()
    if template.count('%%DATA%%') != 1:
        raise ValueError('Expected exactly one public payload slot')
    payload = json.dumps(data, ensure_ascii=False, separators=(',',':')).replace('<', r'\u003c').replace('&',r'\u0026')
    html = template.replace('%%DATA%%', payload).encode()
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    manifest = {'source_commit': commit, 'html_sha256': sha(html), **release}
    receipt = (json.dumps(manifest, indent=2)+'\n').encode()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    allowed = {'index.html','receipt.json','sr-fields-artifact.zip','SHA256SUMS'}
    if any(p.name not in allowed or p.is_symlink() or not p.is_file() for p in out.iterdir()):
        raise ValueError('Choose a dedicated artifact output directory')
    (out/'index.html').write_bytes(html)
    (out/'receipt.json').write_bytes(receipt)
    archive = out/'sr-fields-artifact.zip'
    with zipfile.ZipFile(archive,'w') as bundle:
        for name, content in [('index.html',html),('receipt.json',receipt),('LICENSE',(ROOT/'LICENSE').read_bytes()),
                              ('NOTICE',(ROOT/'NOTICE').read_bytes())]:
            info = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content)
    checksums = ''.join(f'{sha((out/name).read_bytes())}  {name}\n' for name in ('index.html','receipt.json',archive.name))
    (out/'SHA256SUMS').write_text(checksums)
    print(f"Verified {release['slots']:,} slots. HTML SHA-256 {sha(html)}")


if __name__ == '__main__':
    main()
