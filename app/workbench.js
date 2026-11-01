import { $, node, options, json } from './ui.js';
import { t, getLanguage } from './i18n.js';
import { restoreComposition, toggleField, moveField } from './composition.js';

export async function setupWorkbench(pack, presets) {
  const ids = pack.fields.map(f => f.id), storageKey = 'field-observatory-composer-v2';
  let saved;
  try { saved = JSON.parse(localStorage.getItem(storageKey)); } catch { /* Optional preferences. */ }
  const choice = restoreComposition(saved, ids);
  const session = await json('/api/session');
  let compiled = null, generation = 0, pending = false, lastResult = null;
  const post = (path, data) => json(path, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Observatory-Nonce': session.nonce}, body: JSON.stringify(data)});
  const selectedPreset = () => Object.keys(presets).find(key => JSON.stringify(presets[key]) === JSON.stringify(choice.fields)) || 'custom';
  const payload = () => ({preset: selectedPreset(), fields: [...choice.fields], language: choice.language, mode: choice.mode});
  const explainError = error => error.code ? t(error.code) : t('request_failed');
  function persist() {
    try { localStorage.setItem(storageKey, JSON.stringify(choice)); } catch { /* Never persist inputs or replies here. */ }
  }
  function sessionStatus() {
    $('#run').disabled = pending || !compiled || !session.enabled || session.stopped || session.attempted >= session.limit;
    $('#copy-prompt').disabled = $('#download-prompt').disabled = !compiled;
    $('#session-status').textContent = !session.enabled ? t('readOnly') : session.stopped ? t('stopped') : t('requestCount', {used: session.attempted, limit: session.limit});
  }
  function renderSelection() {
    options($('#preset'), [['custom', t('custom')], ...Object.keys(presets).map(id => [id, t(id)])]);
    $('#preset').value = selectedPreset(); $('#mode').value = choice.mode; $('#prompt-language').value = choice.language;
    $('#selection-count').textContent = t('selectionCount', {count: choice.fields.length, total: ids.length});
    $('#selection-note').textContent = choice.mode === 'baseline' ? t('baselineSelection') : !choice.fields.length ? t('emptySelection') : '';
    const picker = $('#field-picker'); picker.replaceChildren();
    for (const field of pack.fields) {
      const row = node('div', undefined, 'picker-row'), label = node('label', undefined, 'field-check');
      const checkbox = node('input'); checkbox.type = 'checkbox'; checkbox.checked = choice.fields.includes(field.id); checkbox.id = 'pick-' + field.id;
      checkbox.onchange = () => select(toggleField(choice.fields, field.id), true, field.id);
      label.append(checkbox, node('span', field.id));
      const only = node('button', t('only')); only.type = 'button'; only.setAttribute('aria-label', `${t('only')}: ${field.id}`);
      only.onclick = () => select([field.id], true, field.id);
      const description = node('details', undefined, 'field-description'), content = field.locales[getLanguage()];
      description.append(node('summary', content.when));
      const list = node('ul'); content.moves.forEach(m => list.append(node('li', m))); description.append(list);
      row.append(label, only, description); picker.append(row);
    }
    const order = $('#field-order'); order.replaceChildren();
    choice.fields.forEach((id, index) => {
      const li = node('li'), name = node('span', id), actions = node('span', undefined, 'order-actions');
      for (const [delta, symbol, key] of [[-1, '↑', 'up'], [1, '↓', 'down']]) {
        const button = node('button', symbol); button.type = 'button'; button.setAttribute('aria-label', t(key, {name: id}));
        button.disabled = index + delta < 0 || index + delta >= choice.fields.length;
        button.onclick = () => select(moveField(choice.fields, id, delta), false, id, key);
        actions.append(button);
      }
      li.append(name, actions); order.append(li);
    });
  }
  function renderResult() {
    if (!lastResult) return;
    $('#trial-result').replaceChildren(node('h3', t('currentReply')), node('div', lastResult.reply || t('noReply'), 'reply'),
      node('p', `${lastResult.status} · ${lastResult.prompt.fields.join(' + ') || t('baseline')} · ${lastResult.prompt.language} · ${lastResult.prompt.mode}`, 'small muted'));
  }
  async function preview() {
    const serial = ++generation;
    compiled = null; sessionStatus();
    $('#prompt-preview').textContent = '';
    if (!choice.fields.length && choice.mode !== 'baseline') {
      $('#workbench-status').textContent = t('emptySelection'); return;
    }
    $('#prompt-preview').textContent = t('loading');
    try {
      const result = await post('/api/preview', payload());
      if (serial !== generation) return;
      compiled = result; $('#prompt-preview').textContent = result.instructions;
      $('#prompt-preview').lang = result.language;
      $('#workbench-status').textContent = t('promptStatus', {hash: result.instructions_sha256.slice(0, 12), language: result.language.toUpperCase()});
    } catch (error) {
      if (serial === generation) { $('#prompt-preview').textContent = ''; $('#workbench-status').textContent = explainError(error); }
    }
    sessionStatus();
  }
  function select(fields, activate = true, focusId = null, focusDirection = null) {
    choice.fields = [...fields];
    if (activate && choice.mode === 'baseline') choice.mode = 'structured';
    persist(); renderSelection(); preview();
    if (focusId) {
      const label = focusDirection ? t(focusDirection, {name: focusId}) : null;
      const button = label && [...$('#field-order').querySelectorAll('button')].find(b => b.getAttribute('aria-label') === label && !b.disabled);
      (button || document.getElementById('pick-' + focusId)).focus();
    }
  }
  $('#preset').onchange = () => { if (presets[$('#preset').value]) select(presets[$('#preset').value]); else renderSelection(); };
  $('#all-on').onclick = () => select(ids);
  $('#clear-fields').onclick = () => select([], false);
  $('#mode').onchange = () => { choice.mode = $('#mode').value; persist(); renderSelection(); preview(); };
  $('#prompt-language').onchange = () => { choice.language = $('#prompt-language').value; persist(); preview(); };
  $('#copy-prompt').onclick = async () => {
    if (!compiled) return;
    try { await navigator.clipboard.writeText(compiled.instructions); $('#workbench-status').textContent = t('copied'); }
    catch { $('#workbench-status').textContent = t('copyFailed'); }
  };
  $('#download-prompt').onclick = () => {
    if (!compiled) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(compiled, null, 2)], {type: 'application/json'}));
    const a = node('a'); a.href = url; a.download = `${compiled.preset}-${compiled.language}-${compiled.mode}.json`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  $('#run').onclick = async () => {
    if (pending || $('#run').disabled) return;
    const submitted = {input: $('#trial-input').value, preset: compiled.preset, fields: [...choice.fields], language: compiled.language, mode: compiled.mode};
    pending = true; sessionStatus(); $('#workbench-status').textContent = t('waiting');
    try {
      lastResult = await post('/api/run', submitted); renderResult();
      $('#workbench-status').textContent = t(lastResult.status === 'completed' ? 'recorded' : 'failureStopped');
    } catch (error) { $('#workbench-status').textContent = explainError(error); }
    finally {
      try { Object.assign(session, await json('/api/session')); } catch { session.stopped = true; }
      pending = false; sessionStatus();
    }
  };
  function refreshLanguage() {
    renderSelection(); renderResult(); sessionStatus();
    if (compiled) $('#workbench-status').textContent = t('promptStatus', {hash: compiled.instructions_sha256.slice(0, 12), language: compiled.language.toUpperCase()});
    else if (!choice.fields.length && choice.mode !== 'baseline') $('#workbench-status').textContent = t('emptySelection');
  }
  renderSelection(); await preview();
  return {refreshLanguage};
}
