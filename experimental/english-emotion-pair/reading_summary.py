"""Summarize the locked reading labels, preserving within-position and repeated-text comparisons."""
from collections import Counter, defaultdict
import csv
from itertools import combinations
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_texts import CASES, RESULTS, RUN
from analyze import save_csv


def main():
    with (RESULTS/'reading.csv').open(newline='') as f:
        labels = list(csv.DictReader(f))
    with (RUN/'replies.csv').open(newline='') as f:
        records = {(r['case'],r['mask'],r['seed']): r for r in csv.DictReader(f)}
    by_position = {}
    repeated = defaultdict(list)
    rows = []
    for case in CASES:
        subset = [r for r in labels if r['case']==case]
        for code in ('OPEN','OFFER','ASSUME','UNCLEAR','MISSING'):
            selected = [r for r in subset if r['code']==code]
            texts = [records[r['case'],r['mask'],r['seed']] for r in selected]
            rows.append({'case':case,'code':code,'count':len(selected),'sampled':len(subset),
                         'with_question_mark':sum(r['question']=='1' for r in texts),
                         'with_listed_emotion':sum(r['emotion_word']=='1' for r in texts)})
        for r in subset:
            key = (case,r['mask'],r['seed'])
            by_position[key]=r['code']
            if r['code'] != 'MISSING':
                repeated[case,records[key]['reply']].append(r['code'])
    save_csv(RESULTS/'reading-counts.csv',rows)
    changes=[]
    for left,right in combinations(CASES,2):
        counts=Counter((code,by_position[right,m,s]) for (case,m,s),code in by_position.items() if case==left)
        for (a,b),n in sorted(counts.items()):
            changes.append({'from_case':left,'to_case':right,'from_code':a,'to_code':b,'matched_slots':n})
    save_csv(RESULTS/'reading-transitions.csv',changes)
    pairs=[(a,b) for group in repeated.values() for a,b in combinations(group,2)]
    result={'reader':'one Codex reading, blinded to Field mask and seed',
            'locked_labels_sha256':json.loads((RUN/'blind-label-lock.json').read_text())['sha256'],
            'repeated_exact_stimulus_reply_pairs':len(pairs),
            'discordant_pairs':sum(a!=b for a,b in pairs),
            'repeated_exact_stimulus_reply_groups':sum(len(v)>1 for v in repeated.values())}
    (RESULTS/'reading-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Summarized',len(labels),'blinded reading slots.')


if __name__=='__main__':
    main()
