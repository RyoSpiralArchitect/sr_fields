"""Build an offline reader that holds a Field set and seed constant across three prompts."""
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_texts import CASES, FIELDS, HERE, P, PREVIOUS, RUN, SEEDS


def main():
    with (RUN/'replies.csv').open(newline='') as f:
        rows={(r['case'],int(r['mask']),int(r['seed'])):(r['reply'] if r['status']=='completed' else '['+r['status']+']')
              for r in csv.DictReader(f)}
    cues={'uncertain':P['replace_historical_text'],**P['cases']}
    data={'cases':CASES,'cues':cues,'fields':FIELDS,'seeds':SEEDS,'dialogue':PREVIOUS['input'],
          'lines':[[[rows[c,m,s] for c in CASES] for s in SEEDS] for m in range(4096)]}
    template=(HERE/'reader.html').read_text()
    if template.count('%%REPLIES%%')!=1: raise ValueError('Missing unique data position')
    encoded=json.dumps(data,ensure_ascii=True,separators=(',',':')).replace('<',r'\u003c').replace('&',r'\u0026')
    dest=RUN/'compare-prompts.html'
    with os.fdopen(os.open(dest,os.O_CREAT|os.O_WRONLY|os.O_TRUNC,0o600),'w',encoding='utf-8') as f:
        f.write(template.replace('%%REPLIES%%',encoded))
    print('Created offline comparison for',len(rows),'recorded slots.')


if __name__=='__main__':
    main()
