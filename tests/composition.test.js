import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { moveField, restoreComposition, toggleField } from '../app/composition.js';
import { dictionaries } from '../app/i18n.js';
const pack = JSON.parse(readFileSync(new URL('../prompts/fields.json', import.meta.url)));
const ids = pack.fields.map(f => f.id);

test('first visit selects all Fields in catalog order with English instructions', () => {
  assert.deepEqual(restoreComposition(null, ids), {fields: ids, mode: 'structured', language: 'en'});
});
test('single, custom, reorder and all-on selections retain explicit order', () => {
  const single = ['HeartField'];
  const pair = toggleField(single, 'TranslationDrive');
  assert.deepEqual(pair, ['HeartField', 'TranslationDrive']);
  assert.deepEqual(single, ['HeartField']);
  assert.deepEqual(moveField(pair, 'TranslationDrive', -1), ['TranslationDrive', 'HeartField']);
  assert.deepEqual(toggleField(pair, 'HeartField'), ['TranslationDrive']);
  assert.deepEqual(restoreComposition({fields: ids}, ids).fields, ids);
});
test('reload preserves custom order, empty selection, language and mode', () => {
  const chosen = {fields: ['GroundField', 'ShieldField'], language: 'ja', mode: 'plain'};
  assert.deepEqual(restoreComposition(chosen, ids), chosen);
  assert.deepEqual(restoreComposition({fields: []}, ids).fields, []);
});
test('invalid saved IDs and duplicate IDs cannot enter a composition', () => {
  for (const fields of [['unknown'], ['HeartField', 'HeartField'], 'HeartField', [null]]) {
    assert.deepEqual(restoreComposition({fields}, ids).fields, ids);
  }
  assert.deepEqual(moveField(['HeartField'], 'HeartField', -1), ['HeartField']);
});
test('every interface key and interpolation token has a paired translation', () => {
  for (const [key, values] of Object.entries(dictionaries)) {
    assert.equal(values.length, 2, key);
    if (typeof values[0] === 'string') {
      assert.ok(values[0].length && values[1].length, key);
      assert.deepEqual([...values[0].matchAll(/\{\w+\}/g)].map(m => m[0]).sort(), [...values[1].matchAll(/\{\w+\}/g)].map(m => m[0]).sort(), key);
    } else assert.equal(values[0].length, values[1].length, key);
  }
  const html = readFileSync(new URL('../app/index.html', import.meta.url), 'utf8');
  for (const [, key] of html.matchAll(/data-i18n(?:-aria)?="([^"]+)"/g)) assert.ok(dictionaries[key], key);
});
