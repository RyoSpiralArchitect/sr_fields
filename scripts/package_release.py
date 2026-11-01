#!/usr/bin/env python3
"""Export only tracked regular files after audit, without Git history or local runs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, '-I', '-S', str(ROOT / 'scripts/audit_public.py')], check=True)
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().strip('\0').split('\0')
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / 'sr_fields.zip'
    receipt = out / 'sr_fields-receipt.json'
    if archive.exists() or receipt.exists():
        raise FileExistsError('Use a clean output destination; existing release artifacts are retained')
    inventory = {}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in names:
            raw = (ROOT / name).read_bytes()
            inventory[name] = hashlib.sha256(raw).hexdigest()
            info = zipfile.ZipInfo('sr_fields/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, raw)
    with receipt.open('x') as handle:
        json.dump({'archive': archive.name, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                   'files': inventory}, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'archive': str(archive.relative_to(ROOT)), 'files': len(inventory), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
