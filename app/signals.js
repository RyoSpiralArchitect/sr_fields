import { $, node, options } from './ui.js';
import { t } from './i18n.js';
const ns = 'http://www.w3.org/2000/svg';
const series = [['latent', '生成した信号', 'one'], ['observation', '観測値', 'two'], ['memory', '履歴 EMA', 'three']];
function svgNode(tag, attrs = {}, text) {
  const el = document.createElementNS(ns, tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  if (text !== undefined) el.textContent = text;
  return el;
}
function chart(title, height, width) {
  const svg = svgNode('svg', {viewBox: `0 0 ${width} ${height}`, class: 'chart', role: 'img', 'aria-label': title});
  svg.append(svgNode('title', {}, title)); return svg;
}
export function setupSignals(data, state, change) {
  options($('#scenario'), data.scenarios.map(s => [s.id, s.label]));
  options($('#threshold'), data.parameters.thresholds.map(t => [t, t === 0 ? '0 · 毎回判断' : t]));
  $('#scenario').onchange = event => change({scenario: event.target.value, bridge: null});
  $('#threshold').onchange = event => change({threshold: Number(event.target.value)});
  for (const [key, name, color] of series) {
    const b = node('button'); b.type = 'button'; b.dataset.series = key;
    const line = node('span', '', 'swatch'); line.style.borderColor = `var(--${color})`;
    b.append(line, node('span', t(key), 'series-name'));
    b.onclick = () => change({hidden: state.hidden.includes(key) ? state.hidden.filter(k => k !== key) : [...state.hidden, key]});
    $('#legend').append(b);
  }
  let lastWidth = 0;
  const draw = () => {
    const s = data.scenarios.find(s => s.id === state.scenario);
    options($('#scenario'), data.scenarios.map(s => [s.id, t(s.id)]));
    options($('#threshold'), data.parameters.thresholds.map(value => [value, value === 0 ? t('always') : value]));
    $('#scenario').value = state.scenario; $('#threshold').value = state.threshold;
    document.querySelectorAll('[data-series]').forEach(b => { b.setAttribute('aria-pressed', String(!state.hidden.includes(b.dataset.series))); b.querySelector('.series-name').textContent = t(b.dataset.series); });
    const margin = state.threshold, n = s.latent.length, warmup = data.parameters.warmup;
    const max = Math.max(1, margin, ...series.flatMap(([key]) => s[key].map(Math.abs))) * 1.08;
    const width = Math.max(260, $('#plot').clientWidth), edge = width - 12;
    lastWidth = width;
    const x = i => 52 + i / (n - 1) * (edge - 52), y = v => 155 - v / max * 125;
    const svg = chart(`${t(s.id)} · ${t('traceTitle')}`, 310, width);
    svg.append(svgNode('rect', {x: 52, y: 25, width: x(warmup) - 52, height: 260, class: 'warmup'}));
    svg.append(svgNode('rect', {x: 52, y: y(margin), width: edge - 52, height: y(-margin) - y(margin), class: 'margin'}));
    for (const v of [-max / 2, 0, max / 2]) {
      svg.append(svgNode('line', {x1: 52, x2: edge, y1: y(v), y2: y(v), class: v === 0 ? 'zero' : 'grid'}));
      svg.append(svgNode('text', {x: 42, y: y(v) + 4, 'text-anchor': 'end'}, v.toFixed(1)));
    }
    for (const t of [0, 128, 256, 383]) svg.append(svgNode('text', {x: x(t), y: 305, 'text-anchor': 'middle'}, t));
    for (const [key, , color] of [series[1], series[0], series[2]]) {
      if (state.hidden.includes(key)) continue;
      svg.append(svgNode('path', {d: s[key].map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' '),
        fill: 'none', stroke: `var(--${color})`, 'stroke-width': key === 'observation' ? 1 : 2,
        opacity: key === 'observation' ? .55 : 1, 'stroke-dasharray': key === 'latent' ? '5 3' : 'none'}));
    }
    $('#plot').replaceChildren(svg);
    const decision = v => Math.abs(v) >= margin ? (v >= 0 ? 1 : -1) : 0;
    const decisions = chart(t('decisionTitle'), 165, width);
    for (const [offset, key, name, color] of [[45, 'observation', t('immediateShort'), 'two'], [120, 'memory', t('memoryShort'), 'three']]) {
      decisions.append(svgNode('text', {x: 3, y: offset + 4}, name));
      for (const [v, label] of [[1, '+'], [0, t('openShort')], [-1, '−']]) {
        const yy = offset - v * 22;
        decisions.append(svgNode('line', {x1: 66, x2: edge, y1: yy, y2: yy, class: 'grid'}));
        decisions.append(svgNode('text', {x: 62, y: yy + 4, 'text-anchor': 'end'}, label));
      }
      s[key].forEach((v, i) => decisions.append(svgNode('circle', {cx: 70 + i / (n - 1) * (edge - 70), cy: offset - decision(v) * 22, r: 1.7, fill: `var(--${color})`, opacity: i < warmup ? .25 : .9})));
    }
    $('#decision-plot').replaceChildren(decisions);
    const metrics = ['observation', 'memory'].map((key, j) => {
      let decided = 0, scored = 0, wrong = 0;
      s[key].slice(warmup).forEach((v, k) => {
        const d = decision(v), truth = s.latent[k + warmup];
        if (d !== 0) { decided++; if (truth !== 0) { scored++; if (d !== Math.sign(truth)) wrong++; } }
      });
      return `${t(j ? 'memoryShort' : 'immediateShort')}: ${t('decided')} ${(100 * decided / (n - warmup)).toFixed(1)}% / ${t('errorRate')} ${scored ? (100 * wrong / scored).toFixed(1) + '%' : t('undefined')}`;
    });
    $('#signal-metrics').replaceChildren(...metrics.map(text => node('div', text)));
  };
  new ResizeObserver(() => {
    if (!$('#panel-signals').hidden && Math.max(260, $('#plot').clientWidth) !== lastWidth) draw();
  }).observe($('#plot'));
  return draw;
}
