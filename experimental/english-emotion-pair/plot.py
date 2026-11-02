"""Render matched percentage-point differences on a common colour scale."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE/'results'
RUN = HERE.parents[1]/'.runs'/HERE.name


def main():
    fields = json.loads((HERE.parent/'english-powerset'/'protocol.json').read_text())['fields_in_bit_order']
    with (RESULTS/'field-effects.csv').open(newline='') as f:
        lookup = {(r['field'],r['case'],r['measure']):float(r['delta']) for r in csv.DictReader(f) if r['delta']!=''}
    panels = [('Question mark','question',['uncertain','embarrassed','happy']),
              ('Invitation phrase','invitation',['uncertain','embarrassed','happy']),
              ("A’s exact emotion word",'echo_exact',['embarrassed','happy'])]
    matrices = [np.array([[lookup.get((field,case,metric),np.nan) for case in cases] for field in fields])
                for _,metric,cases in panels]
    with (RESULTS/'rates.csv').open(newline='') as f:
        n=sum(int(r['n']) for r in csv.DictReader(f) if r['measure']=='question')
    extent = max(10,np.ceil(max(np.nanmax(abs(x)) for x in matrices)/5)*5)
    cmap = LinearSegmentedColormap.from_list('field-shift',['#7b3855','#e4bac2','#f8f7f0','#a6d8c9','#145c61'])
    norm = Normalize(-extent,extent)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','svg.hashsalt':'sr-affect-comparison'})
    fig,axes=plt.subplots(1,3,figsize=(12,7.5),gridspec_kw={'width_ratios':[3,3,2]},sharey=True)
    fig.patch.set_facecolor('#fbfaf6')
    fig.subplots_adjust(left=.17,right=.97,top=.78,bottom=.22,wspace=.14)
    fig.text(.045,.93,'What changes when a Field is added?',size=22,weight='bold',color='#20393a')
    fig.text(.046,.866,f'GPT-4.1 mini  /  {n:,} eligible replies  /  same dialogue, three versions of A’s last turn',
             size=12,color='#506566')
    short={'uncertain':'Uncertain','embarrassed':'Embarrassed','happy':'Happy'}
    for ax,(title,metric,cases),matrix in zip(axes,panels,matrices):
        ax.imshow(matrix,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
        ax.set_title(title,fontsize=14,weight='bold',loc='left',pad=12)
        ax.set_xticks(range(len(cases)),labels=[short[c] for c in cases],size=9)
        ax.set_yticks(range(len(fields)),labels=fields,size=10)
        ax.tick_params(length=0,pad=5)
        for j in range(len(cases)):
            for i in range(len(fields)):
                value=matrix[i,j]
                if not np.isfinite(value): continue
                label=f'{value:+.1f}' if abs(value)>=.05 else '0.0'
                ax.text(j,i,label,ha='center',va='center',size=9,
                        color='white' if abs(value)>.72*extent else '#163232')
        for side in ax.spines.values(): side.set_visible(False)
    cax=fig.add_axes([.29,.126,.48,.020])
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',
                 ticks=[-extent,-extent/2,0,extent/2,extent]).ax.tick_params(labelsize=8,length=2)
    fig.text(.046,.052,'Numbers are percentage-point changes, Field ON minus OFF, matched on the other 11 Fields and seed.',
             fontsize=10,color='#405253')
    fig.text(.046,.025,'Uncertain is the earlier run. Exact emotion-word reuse is defined only for the two explicit feelings.',
             fontsize=9,color='#506566')
    svg=RESULTS/'field-by-prompt.svg'
    fig.savefig(svg,metadata={'Date':None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    fig.savefig(RUN/'field-by-prompt.png',dpi=145)
    plt.close(fig)


if __name__=='__main__':
    main()
