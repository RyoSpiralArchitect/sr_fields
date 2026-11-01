import { $, node, options } from './ui.js';
import { t } from './i18n.js';
const arms = {immediate: 'immediate', optional: 'optional', fixed_wait: 'fixed_wait'};
const apiArms = {baseline: 'baseline', plain_rules: 'plain_rules', field_pack: 'field_pack'};
function original(tag, text, className) { const el = node(tag, text, className); el.lang = 'ja'; return el; }
export function setupRecords(dialogue, pilot, state, change) {
  options($('#dialogue-case'), dialogue.cases.map(c => [c.id, c.title]));
  options($('#pilot-case'), pilot.cases.map(c => [c.id, c.title]));
  $('#dialogue-case').onchange = e => change({dialogueCase: e.target.value, stage: 1, bridge: null});
  $('#stage').onchange = e => change({stage: Number(e.target.value), bridge: null});
  $('#pilot-case').onchange = e => change({apiCase: e.target.value, bridge: null});
  return {
    dialogue() {
      const c = dialogue.cases.find(c => c.id === state.dialogueCase), host = $('#dialogue-content');
      options($('#dialogue-case'), dialogue.cases.map((c, i) => [c.id, t('dialogueTitles')[i]]));
      $('#dialogue-case').value = c.id; $('#stage').value = state.stage;
      const inputs = original('ol', undefined, 'inputs');
      c.turns.slice(0, state.stage).forEach(t => inputs.append(node('li', t.text)));
      host.replaceChildren(inputs, original('p', c.question));
      Object.entries(c.labels).forEach(([k, v]) => host.append(original('div', `${k}：${v}`, 'small')));
      const table = node('table'), head = node('thead'), hr = node('tr'), body = node('tbody');
      table.append(node('caption', t('trajectory')));
      ['reader', 'stageOne', 'stageTwo', 'stageThree'].forEach(s => { const th = node('th', t(s)); th.scope = 'col'; hr.append(th); });
      head.append(hr); table.append(head, body);
      for (const [name, values] of [['author', c.turns.map(t => t.reference)], ...Object.entries(arms).map(([key, name]) => [name, c.responses[key].map(r => r.label)])]) {
        const tr = node('tr'), th = node('th', t(name)); th.scope = 'row'; tr.append(th);
        values.forEach((v, i) => tr.append(node('td', i < state.stage ? v : '—'))); body.append(tr);
      }
      host.append(table, node('p', t('actualReplies', {stage: state.stage}), 'muted small'));
      const grid = node('div', undefined, 'reply-grid');
      Object.entries(arms).forEach(([key, name]) => {
        const r = c.responses[key][state.stage - 1], col = node('section'), detail = node('details');
        detail.append(node('summary', t('reason')), original('p', r.reason, 'small reply'));
        col.append(node('h3', t(name)), original('div', r.reply, 'reply'), detail); grid.append(col);
      }); host.append(grid);
    },
    pilot() {
      const c = pilot.cases.find(c => c.id === state.apiCase), host = $('#pilot-content');
      options($('#pilot-case'), pilot.cases.map((c, i) => [c.id, t('pilotTitles')[i]]));
      $('#pilot-case').value = c.id;
      host.replaceChildren(original('blockquote', c.input, 'input-quote'));
      const grid = node('div', undefined, 'reply-grid');
      Object.entries(apiArms).forEach(([key, name]) => {
        const r = c.responses[key], col = node('section'); col.append(node('h3', t(name)));
        col.append(r.reply ? original('div', r.reply, 'reply') : node('div', t('missing'), 'muted reply')); grid.append(col);
      });
      host.append(grid, node('p', pilot.model, 'small muted'));
    }
  };
}
