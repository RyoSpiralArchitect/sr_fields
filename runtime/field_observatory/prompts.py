"""Compile public semantic cards. No access to private YAML is needed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODES = ('baseline', 'plain', 'structured')
LANGUAGES = ('en', 'ja')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def catalog(root=ROOT):
    pack = json.loads((root / 'prompts/fields.json').read_text())
    presets = json.loads((root / 'prompts/presets.json').read_text())
    if pack.get('schema_version') != 2 or pack.get('languages') != list(LANGUAGES):
        raise ValueError('Unsupported prompt catalog schema or languages')
    fields = pack.get('fields', [])
    ids = [f.get('id') for f in fields]
    if not ids or len(ids) != len(set(ids)) or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError('Field IDs must be distinct nonempty strings')
    for f in fields:
        if set(f) != {'id', 'locales', 'origin', 'status'}:
            raise ValueError('Only public semantic card properties are accepted')
        if set(f['locales']) != set(LANGUAGES):
            raise ValueError('Every Field requires both English and Japanese')
        for localized in f['locales'].values():
            if set(localized) != {'when', 'moves'}:
                raise ValueError('Localized cards contain only scope and moves')
            if not isinstance(localized['when'], str) or not localized['when'] or not isinstance(localized['moves'], list) or not localized['moves']:
                raise ValueError('Each Field needs a scope and response moves')
            if any(not isinstance(m, str) or not m for m in localized['moves']):
                raise ValueError('Moves must be nonempty strings')
        if len(f['locales']['en']['moves']) != len(f['locales']['ja']['moves']):
            raise ValueError('Localized move sequences must be aligned')
        if f['status'] != 'proposed_operational_interpretation':
            raise ValueError('Cards must retain their interpretation status')
    for names in presets.values():
        if not isinstance(names, list) or not names or len(set(names)) != len(names) or set(names) - set(ids):
            raise ValueError('Preset refers to unknown or repeated Fields')
    return pack, presets


def compile_prompt(preset='quiet-dialogue', mode='structured', root=ROOT, *, language='en', field_ids=None):
    pack, presets = catalog(root)
    if not isinstance(preset, str) or (preset not in presets and preset != 'custom') or mode not in MODES or language not in LANGUAGES:
        raise ValueError('Unknown preset, prompt mode or language')
    by_id = {f['id']: f for f in pack['fields']}
    if field_ids is None:
        if preset == 'custom':
            raise ValueError('Custom selections require explicit Field IDs')
        field_ids = presets[preset]
    if not isinstance(field_ids, list) or any(not isinstance(i, str) or i not in by_id for i in field_ids) or len(set(field_ids)) != len(field_ids):
        raise ValueError('Select distinct known Field IDs in the desired order')
    if not field_ids and mode != 'baseline':
        raise ValueError('Choose at least one Field, or use baseline mode')
    source_preset = preset if presets.get(preset) == field_ids else 'custom'
    selected = [{'id': i, **by_id[i]['locales'][language]} for i in field_ids]
    base = (root / f'prompts/base.{language}.md').read_text().strip()
    if mode == 'baseline':
        instructions = base
        selected = []
    elif mode == 'plain':
        instructions = base + '\n\n' + '\n\n'.join(f['when'] + '\n' + '\n'.join('- ' + m for m in f['moves']) for f in selected)
    else:
        # Same scopes and moves as plain mode; names and JSON structure differ.
        instructions = base + '\n\n' + json.dumps({'fields': [
            {'id': f['id'], 'when': f['when'], 'moves': f['moves']} for f in selected]}, ensure_ascii=False, indent=2)
    return {'preset': source_preset, 'mode': mode, 'language': language,
            'fields': [f['id'] for f in selected], 'instructions': instructions,
            'instructions_sha256': digest(instructions.encode())}
