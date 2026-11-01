import { $, node, json } from './ui.js';
import { setupSignals } from './signals.js';
import { setupRecords } from './records.js';
import { setupWorkbench } from './workbench.js';
import { t, setLanguage } from './i18n.js';
const views = ['signals', 'dialogue', 'pilot', 'workbench'];
try {
  const [signals, dialogue, pilot, bridges, fields, presets] = await Promise.all([
    '/data/signals.json', '/data/dialogue.json', '/data/api-pilot.json', '/data/bridges.json', '/prompts/fields.json', '/prompts/presets.json'
  ].map(path => json(path)));
  const state = {view: 'signals', scenario: 'walk', threshold: .35, hidden: [], dialogueCase: 'c10', stage: 1, apiCase: 'c01', bridge: null, uiLanguage: 'en'};
  let workbench;
  try {
    const saved = JSON.parse(localStorage.getItem('field-observatory-v1') || '{}');
    const choices = {view: views, uiLanguage: ['en', 'ja'], scenario: signals.scenarios.map(s => s.id), threshold: signals.parameters.thresholds,
      dialogueCase: dialogue.cases.map(c => c.id), stage: [1, 2, 3], apiCase: pilot.cases.map(c => c.id), bridge: bridges.map(b => b.id)};
    Object.entries(choices).forEach(([k, values]) => { if (values.includes(saved[k])) state[k] = saved[k]; });
    if (Array.isArray(saved.hidden)) state.hidden = saved.hidden.filter(k => ['latent', 'observation', 'memory'].includes(k));
  } catch { /* Invalid or unavailable browser storage uses defaults. Input text is never saved here. */ }
  function change(values) {
    Object.assign(state, values); render();
    try { localStorage.setItem('field-observatory-v1', JSON.stringify(state)); } catch { /* Optional UI state. */ }
  }
  setLanguage(state.uiLanguage);
  $('#ui-language').value = state.uiLanguage;
  $('#ui-language').onchange = () => {
    setLanguage($('#ui-language').value);
    change({uiLanguage: $('#ui-language').value});
    workbench?.refreshLanguage();
  };
  const drawSignals = setupSignals(signals, state, change), records = setupRecords(dialogue, pilot, state, change);
  for (const bridge of bridges) {
    const button = node('button', t(bridge.id)); button.dataset.bridge = bridge.id;
    button.onclick = () => change({scenario: bridge.scenario, dialogueCase: bridge.dialogueCase, stage: bridge.stage, apiCase: bridge.apiCase, bridge: bridge.id});
    $('#bridges').append(button);
  }
  const tabs = [...document.querySelectorAll('[data-view]')];
  for (const tab of tabs) {
    tab.onclick = () => change({view: tab.dataset.view});
    tab.onkeydown = event => {
      const index = tabs.indexOf(tab);
      const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null;
      if (next !== null) { event.preventDefault(); tabs[next].focus(); change({view: tabs[next].dataset.view}); }
    };
  }
  function render() {
    tabs.forEach(tab => { const active = state.view === tab.dataset.view; tab.setAttribute('aria-selected', String(active)); tab.tabIndex = active ? 0 : -1; });
    views.forEach(view => { $(`#panel-${view}`).hidden = view !== state.view; });
    document.querySelectorAll('[data-bridge]').forEach(b => { b.setAttribute('aria-pressed', String(b.dataset.bridge === state.bridge)); b.textContent = t(b.dataset.bridge); });
    if (state.view === 'signals') drawSignals();
    else if (state.view === 'dialogue') records.dialogue();
    else if (state.view === 'pilot') records.pilot();
  }
  render();
  workbench = await setupWorkbench(fields, presets);
} catch (error) {
  $('#error').hidden = false; $('#error').textContent = `${t('loadError')} ${error.message}`;
}
