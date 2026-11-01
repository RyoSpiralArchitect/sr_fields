#!/usr/bin/env python3
"""Audit the tracked release tree and its data inventory without reading secrets."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'credential-like token': re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}'),
    'private home path': re.compile(r'/(?:Users|home)/[A-Za-z][^\s"\']*'),
    'provider response identifier': re.compile(r'resp_[a-f0-9]{20,}'),
    'session identifier': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'),
    'private source excerpt property': re.compile(r'"(?:excerpts|source_sha256|source_lines)"\s*:'),
    'private key material': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}


def public_files():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    files = [ROOT / p for p in result.stdout.decode().split('\0') if p]
    if not files:
        raise ValueError('Stage the intended public tree before auditing')
    return files


def audit():
    failures = []
    files = public_files()
    for path in files:
        name = str(path.relative_to(ROOT))
        if path.is_symlink() or not path.is_file():
            failures.append([name, 'non-regular file']); continue
        if any(part in {'.runs', '.private', 'originals', 'sources', '__pycache__', '.venv'} or part.startswith('.env') for part in path.relative_to(ROOT).parts):
            failures.append([name, 'private or generated path'])
        if path.suffix in ('.yaml', '.yml') and name != '.github/workflows/checks.yml':
            failures.append([name, 'unapproved YAML'])
        text = path.read_text()
        for label, pattern in PATTERNS.items():
            if pattern.search(text): failures.append([name, label])
    manifest = json.loads((ROOT / 'data/manifest.json').read_text())
    for name, sha in manifest['files'].items():
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT / 'data') or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            failures.append([name, 'data inventory mismatch'])
    if failures:
        print(json.dumps({'status': 'failed', 'findings': failures}, indent=2))
        return 1
    print(json.dumps({'status': 'passed', 'tracked_files': len(files), 'data_files': len(manifest['files']),
                      'scope': 'pattern and inventory checks; review remains necessary'}))
    return 0


if __name__ == '__main__':
    sys.exit(audit())
