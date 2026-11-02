"""Draw the primary paired contrasts from the aggregate CSV. Requires Matplotlib."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
LOCAL = HERE.parents[1] / '.runs' / 'english-powerset'


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    summary = json.loads((RESULTS / 'summary.json').read_text())
    fields = protocol['fields_in_bit_order']
    with (RESULTS / 'field-contrasts.csv').open(newline='') as handle:
        records = {(r['field'], r['measure']): r for r in csv.DictReader(handle)}
    background, ink, soft = '#fbfaf6', '#172d30', '#52676a'
    panels = [('question', 'Question mark', 'percentage points', '#176a77'),
              ('emotion_word', 'Listed emotion word', 'percentage points', '#8a4776'),
              ('words', 'Reply length', 'words per reply', '#a55e29')]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'text.color': ink,
                         'axes.labelcolor': soft, 'xtick.color': soft, 'ytick.color': ink,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'english-powerset-primary'})
    fig, axes = plt.subplots(1, 3, figsize=(12.9, 7.2), sharey=True)
    fig.patch.set_facecolor(background)
    fig.subplots_adjust(left=.17, right=.974, top=.76, bottom=.18, wspace=.23)
    fig.text(.045, .925, 'What changes when one Field is switched on?', fontsize=23, fontweight='bold')
    eligible = summary['statuses'].get('completed', 0)
    fig.text(.047, .857, f'One English dialogue   /   GPT-4.1 mini   /   {eligible:,} eligible replies   /   three seeds',
             fontsize=12.5, color=soft)
    for ax, (key, title, unit, color) in zip(axes, panels):
        ax.set_facecolor(background)
        ax.set_axisbelow(True)
        for i in range(0, len(fields), 2):
            ax.axhspan(i-.48, i+.48, color='#f0f0e9', zorder=0)
        extent = 0
        for i, field in enumerate(fields):
            row = records[field, key]
            if row['delta'] == '':
                continue
            center = float(row['delta'])
            seeds = [float(row[f'delta_s{s}']) for s in protocol['seeds'] if row[f'delta_s{s}'] != '']
            lo, hi = min(seeds), max(seeds)
            extent = max(extent, abs(lo), abs(hi), abs(center))
            ax.plot([lo, hi], [i, i], color=color, lw=2.0, zorder=3)
            ax.plot([lo, hi], [i, i], '|', color=color, markersize=6.3, zorder=4)
            ax.scatter(center, i, s=44, color=color, edgecolor=background, linewidth=.7, zorder=5)
        span = max(extent*1.13, .5)
        ax.set_xlim(-span, span)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, symmetric=True, steps=[1, 2, 2.5, 5, 10]))
        ax.grid(axis='x', color='#dce2dc', lw=.65)
        ax.axvline(0, color='#667a78', lw=1.2)
        ax.set_title(title, loc='left', fontsize=14, pad=11, fontweight='bold', color=color)
        ax.set_xlabel(unit, fontsize=10, labelpad=7)
        ax.tick_params(length=0, pad=6)
        for side in ax.spines.values():
            side.set_visible(False)
    axes[0].set_yticks(range(len(fields)), labels=fields)
    axes[0].set_ylim(len(fields)-.48, -.52)
    for label in axes[0].get_yticklabels():
        label.set_fontsize(10.5)
    fig.text(.047, .082, 'Dot: average ON minus OFF with the same other 11 Fields and seed.  Whisker: range of the three seed averages.',
             color=ink, fontsize=10.4)
    fig.text(.047, .048, 'Axes use separate scales.  Word and punctuation markers describe these replies; they do not score dialogue quality.',
             color=soft, fontsize=9.8)
    svg = RESULTS / 'primary-contrasts.svg'
    fig.savefig(svg, format='svg', metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    LOCAL.mkdir(parents=True, exist_ok=True)
    fig.savefig(LOCAL / 'primary-contrasts.png', format='png', dpi=145)
    plt.close(fig)


if __name__ == '__main__':
    main()
