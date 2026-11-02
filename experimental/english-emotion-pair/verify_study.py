"""Independently check full matched comparisons from the exported per-slot table."""
import csv
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_texts import CASES, FIELDS, METRICS, OLD_METRICS, PARENT, RESULTS, SEEDS


def table(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def close(a,b):
    if a is None or a=='':
        return b is None or b==''
    return b is not None and b!='' and math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-10)


def main():
    slots = table(RESULTS/'slot-features.csv')
    expected = {(c,m,s) for c in CASES for m in range(4096) for s in SEEDS}
    if len(slots)!=len(expected) or {(r['case'],int(r['mask']),int(r['seed'])) for r in slots}!=expected:
        raise ValueError('Unexpected slot identities')
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE t (c TEXT, m INTEGER, s INTEGER, '+','.join(k+' REAL' for k in METRICS)+', PRIMARY KEY(c,m,s))')
    sql = 'INSERT INTO t VALUES ('+','.join('?' for _ in range(3+len(METRICS)))+')'
    db.executemany(sql,((r['case'],int(r['mask']),int(r['seed']),*[None if r[k]=='' else int(r[k]) for k in METRICS])
                        for r in slots if r['status']=='completed'))

    def check_group(rows, query, keys, args):
        # Each SQL join enforces a complete block. NULL in a measure stays out of its own denominator.
        by_seed = {v[0]:v[1:] for v in db.execute(query,args)}
        for pos,k in enumerate(keys):
            r = rows[k]
            scale = 1 if k=='words' else 100
            if r['unit']!=('words' if k=='words' else 'pp'):
                raise ValueError('Measurement unit differs')
            total = count = 0
            for s in SEEDS:
                found = by_seed.get(s,[0,None]*len(keys))
                n, value = found[2*pos:2*pos+2]
                if n!=int(r[f'n_s{s}']) or not close(value*scale/n if n else None,r[f'delta_s{s}']):
                    raise ValueError('Seed-specific SQL comparison differs: '+str(r))
                total += value or 0
                count += n
            if count!=int(r['matched_blocks']) or not close(scale*total/count if count else None,r['delta']):
                raise ValueError('Pooled SQL comparison differs: '+str(r))

    def validate(filename, grouping, make_query, metrics):
        groups = {}
        for row in table(RESULTS/(filename+'.csv')):
            key = tuple(row[g] for g in grouping)
            groups.setdefault(key,{})[row['measure']]=row
        for group,rows in groups.items():
            joins,where,args,expression = make_query(*group)
            values = []
            for m in metrics:
                diff = expression.format(k=m)
                values.extend([f'COUNT({diff})',f'SUM({diff})'])
            query='SELECT a.s,'+','.join(values)+' FROM t a '+joins+' WHERE '+where+' GROUP BY a.s'
            check_group(rows,query,metrics,args)
        return len(groups)*len(metrics)

    def primary(case,field):
        bit=1<<FIELDS.index(field)
        return ('JOIN t b ON a.c=b.c AND a.s=b.s AND b.m=a.m+?', 'a.c=? AND (a.m & ?)=0',
                [bit,case,bit],'(b.{k}-a.{k})')

    def stimulus(first,second):
        return ('JOIN t b ON a.m=b.m AND a.s=b.s','a.c=? AND b.c=?',[first,second],'(b.{k}-a.{k})')

    def modulation(first,second,field):
        bit=1<<FIELDS.index(field)
        return ('JOIN t b ON b.c=a.c AND b.s=a.s AND b.m=a.m+? '
                'JOIN t d ON d.s=a.s AND d.m=a.m AND d.c=? JOIN t e ON e.c=d.c AND e.s=a.s AND e.m=b.m',
                'a.c=? AND (a.m & ?)=0',[bit,second,first,bit],'(e.{k}-d.{k}-b.{k}+a.{k})')

    def interactions(case,first,second):
        x,y=1<<FIELDS.index(first),1<<FIELDS.index(second)
        return ('JOIN t b ON b.c=a.c AND b.s=a.s AND b.m=a.m+? JOIN t d ON d.c=a.c AND d.s=a.s AND d.m=a.m+? '
                'JOIN t e ON e.c=a.c AND e.s=a.s AND e.m=a.m+?',
                'a.c=? AND (a.m & ?)=0',[x,y,x+y,case,x+y],'(e.{k}-b.{k}-d.{k}+a.{k})')

    n=validate('prompt-differences',['from_case','to_case'],stimulus,METRICS)
    n+=validate('field-effects',['case','field'],primary,METRICS)
    n+=validate('field-by-prompt',['from_case','to_case','field'],modulation,METRICS)
    n+=validate('field-pairs',['case','first','second'],interactions,OLD_METRICS)
    if n != (3+36+36)*len(METRICS)+198*len(OLD_METRICS):
        raise ValueError('Unexpected comparison count')

    for new,old,fields in [('field-effects','field-contrasts',['field']),('field-pairs','pair-interactions',['first','second'])]:
        reference = {tuple(r[g] for g in fields+[ 'measure']):r for r in table(PARENT/'results'/(old+'.csv'))}
        selected = [r for r in table(RESULTS/(new+'.csv')) if r['case']=='uncertain' and r['measure'] in OLD_METRICS]
        if len(selected)!=len(reference):
            raise ValueError('Historical comparison coverage differs')
        for r in selected:
            ref=reference[tuple(r[g] for g in fields+['measure'])]
            if not close(r['delta'],ref['delta']) or r['matched_blocks']!=ref['matched_sets']:
                raise ValueError('Historical reference differs')
    print(f'Checked {len(slots):,} slot keys, {n:,} pooled contrasts with per-seed counts, and the previous 624 contrasts.')


if __name__ == '__main__':
    main()
