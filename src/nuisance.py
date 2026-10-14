"""Paper 3: reducing nuisance alarms of label-free bearing early-warning rules (protocol in PROTOCOL.md).
Usage: python nuisance.py <pooled.csv from paper 2> <IMS data dir with test1-3.csv> <out dir>"""
import sys, json, numpy as np
from scipy.stats import wilcoxon, binomtest
from p3lib import *
POOLED, IMSD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
B = load_failed(POOLED); NF = load_ims_nonfailed(IMSD)
print('failed bearings', len(B), '| non-failed IMS', len(NF), flush=True)
DEF = {'M0': {}, 'M1': {}, 'M2': {}, 'M3': {}, 'M4': {}, 'M5': {}, 'M6': {}, 'M7': {}}
R = dict(protocol='PROTOCOL.md', costs=dict(Cp=Cp, Cf=Cf, Cfa=Cfa0, EL=EL, age_opt=AGE, rtf=RTF))

# ---- 1. defaults, pooled + per dataset + paired tests + non-failed control
main, rowsets = {}, {}
for mth, kw in DEF.items():
    rows = evaluate(B, mth, **kw); rowsets[mth] = rows
    s = summarize(rows); s['by_dataset'] = {ds: summarize([r for r in rows if r['dataset'] == ds]) for ds in ['IMS', 'XJTU-SY', 'FEMTO']}
    nf = evaluate(NF, mth, **kw)
    s['nonfailed'] = dict(n=len(nf), nuis_total=int(sum(r['nuis'] for r in nf)), bearings_any_alarm_before_final=int(sum(r['early_alarm'] for r in nf)),
                          bearings_nuis=int(sum(r['nuis'] > 0 for r in nf)))
    if mth != 'M0':
        a0 = np.array([r['nuis'] for r in rowsets['M0']]); a1 = np.array([r['nuis'] for r in rows])
        s['wilcoxon_p'] = float(wilcoxon(a0, a1).pvalue) if np.any(a0 != a1) else 1.0
        d0 = np.array([r['det'] for r in rowsets['M0']]); d1 = np.array([r['det'] for r in rows])
        b01, b10 = int((d0 & ~d1).sum()), int((~d0 & d1).sum())
        s['mcnemar'] = dict(lost=b01, gained=b10, p=float(binomtest(b01, b01 + b10).pvalue) if b01 + b10 else 1.0)
    s['units'] = rows; main[mth] = s
    print(mth, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k not in ('units', 'by_dataset', 'ci')}, flush=True)
R['main'] = main

# ---- 2. sensitivity of defaults
sens = {}
for lab, kw2, ml, cfa in [('k5', dict(k=5), MINLEAD, None), ('lead2pct', {}, 0.02, None), ('cfa1000', {}, MINLEAD, 1000.0), ('cfa5000', {}, MINLEAD, 5000.0)]:
    sens[lab] = {}
    for mth in DEF:
        rows = evaluate(B, mth, minlead=ml, **kw2); s = summarize(rows)
        if cfa: s['cost_pess'] = cost(rows, cfa); s['cost_opt'] = cost(rows, cfa, 'opt')
        sens[lab][mth] = s
R['sensitivity'] = sens

# ---- 3. grid + leave-one-dataset-out selection by pessimistic empirical cost
CG = [round(1.10 + 0.05 * i, 2) for i in range(19)]
grid = []
for c in CG:
    grid += [('M0', dict(c=c)), ('M5', dict(c=c))]
    grid += [('M1', dict(c=c, m=m)) for m in (6, 8, 10)]
    grid += [('M2', dict(c=c, w=w)) for w in (5, 10, 20)]
    grid += [('M3', dict(c=c, lam=l)) for l in (0.05, 0.1, 0.2)]
    grid += [('M4', dict(c=c, off=o)) for o in (0.85, 0.90, 0.95)]
    grid += [('M6', dict(c=c, off=o)) for o in (0.85, 0.90, 0.95)]
    grid += [('M7', dict(c=c, H=h)) for h in (3, 5, 10)]
G = []
for mth, kw in grid:
    rows = evaluate(B, mth, **kw); G.append(dict(method=mth, kw=kw, rows=rows))
print('grid configs', len(G), flush=True)
def sub(rows, dss): return [r for r in rows if r['dataset'] in dss]
DS = ['IMS', 'XJTU-SY', 'FEMTO']
lodo = {}
for hold in DS:
    tr = [d for d in DS if d != hold]
    best = min(G, key=lambda g: cost(sub(g['rows'], tr)))
    te = sub(best['rows'], [hold]); s = summarize(te)
    m0 = next(g for g in G if g['method'] == 'M0' and g['kw']['c'] == 1.2); s0 = summarize(sub(m0['rows'], [hold]))
    lodo[hold] = dict(method=best['method'], kw=best['kw'], train_cost=cost(sub(best['rows'], tr)), test=s, test_M0_default=s0)
R['lodo'] = lodo
bestper = {}
for mth in DEF:
    gs = [g for g in G if g['method'] == mth]; b = min(gs, key=lambda g: cost(g['rows']))
    bestper[mth] = dict(kw=b['kw'], **summarize(b['rows']))
R['best_in_sample_per_method'] = bestper
R['grid_summary'] = [dict(method=g['method'], **g['kw'], **{k: v for k, v in summarize(g['rows']).items() if k != 'ci'}) for g in G]
json.dump(R, open(f'{OUT}/paper3.json', 'w'), indent=1, default=float)
print('LODO', json.dumps({h: (v['method'], v['kw'], v['test']['detected'], v['test']['n'], v['test']['nuis_mean'], round(v['test']['cost_pess']),
                               v['test_M0_default']['detected'], v['test_M0_default']['nuis_mean'], round(v['test_M0_default']['cost_pess'])) for h, v in lodo.items()}))
print('best per method', json.dumps({m: (v['kw'], v['detected'], round(v['nuis_mean'], 2), round(v['cost_pess']), round(v['cost_opt'])) for m, v in bestper.items()}))
