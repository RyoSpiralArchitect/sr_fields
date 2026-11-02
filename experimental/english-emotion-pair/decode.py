"""Measure how well wording predicts the two explicit prompts on held-out groups."""
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_texts import P, RESULTS, RUN
from analyze import save_csv
from measures import lexical_tokens, masked_tokens


def bucket(namespace, value, modulus):
    text = f"{P['fold_salt']}|{namespace}|{value}"
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], 'big') % modulus


def scores(truth, decision):
    predicted = (decision > 0).astype(int)
    tn, fp, fn, tp = confusion_matrix(truth,predicted,labels=[0,1]).ravel()
    return {'n':len(truth), 'embarrassed_n':int(tn + fp), 'happy_n':int(fn + tp),
            'correct_embarrassed':int(tn), 'correct_happy':int(tp),
            'balanced_accuracy':float(balanced_accuracy_score(truth,predicted)),
            'macro_f1':float(f1_score(truth,predicted,average='macro')),
            'roc_auc':float(roc_auc_score(truth,decision))}


def main():
    with (RUN/'replies.csv').open(newline='') as f:
        records = {(int(r['mask']),int(r['seed']),r['case']): r['reply'] for r in csv.DictReader(f)
                   if r['case'] != 'uncertain' and r['status']=='completed'}
    raw,masked,y,swapped,mask_folds,wording_folds = [],[],[],[],[],[]
    for mask, seed in sorted({(m,s) for m,s,_ in records}):
        if not all((mask,seed,c) in records for c in ('embarrassed','happy')):
            continue
        for label,case in enumerate(('embarrassed','happy')):
            line = records[mask,seed,case]
            raw.append(' '.join(lexical_tokens(line)))
            neutral = ' '.join(masked_tokens(line))
            masked.append(neutral)
            y.append(label)
            swapped.append(label ^ bucket('label-swap',mask,2))
            mask_folds.append(bucket('mask',mask,5))
            wording_folds.append(bucket('masked-wording',neutral,5))
    y, swapped = np.array(y),np.array(swapped)
    results = []
    for holdout,folds in [('mask',mask_folds),('wording',wording_folds)]:
        folds = np.array(folds)
        for language,forms in [('intact',raw),('cue-removed',masked)]:
            inputs = np.array(forms,dtype=object)
            all_scores = {k:np.full(len(y),np.nan) for k in ('observed','swapped')}
            for fold in range(5):
                test = folds==fold
                if not test.any() or len(set(y[test]))!=2:
                    raise ValueError('A test fold lacks both classes')
                if holdout=='wording' and (set(np.array(masked,dtype=object)[test]) & set(np.array(masked,dtype=object)[~test])):
                    raise ValueError('A masked wording leaked across folds')
                vectorizer = TfidfVectorizer(tokenizer=str.split,token_pattern=None,lowercase=False,
                                             min_df=5,ngram_range=(1,2),sublinear_tf=True)
                training = vectorizer.fit_transform(inputs[~test])
                testing = vectorizer.transform(inputs[test])
                for tag,truth in [('observed',y),('swapped',swapped)]:
                    classifier = LogisticRegression(C=1, max_iter=1000,solver='liblinear',random_state=0)
                    classifier.fit(training,truth[~test])
                    s = classifier.decision_function(testing)
                    all_scores[tag][test] = s
                    results.append({'holdout':holdout,'words':language,'labels':tag,'fold':fold,
                                    **scores(truth[test],s)})
            for tag,truth in [('observed',y),('swapped',swapped)]:
                if not np.all(np.isfinite(all_scores[tag])):
                    raise ValueError('Missing out-of-fold score')
                results.append({'holdout':holdout,'words':language,'labels':tag,'fold':'all',
                                **scores(truth,all_scores[tag])})
    save_csv(RESULTS/'decoding.csv',results)
    (RESULTS/'decoding-runtime.json').write_text(json.dumps({'python':platform.python_version(),
            'numpy':np.__version__,'sklearn':sklearn.__version__},indent=2)+'\n')
    print('Computed paired classification and swapped-label control on', len(y), 'out-of-fold replies.')


if __name__ == '__main__':
    main()
