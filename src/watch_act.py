"""Paper 4: watch-and-act replacement rules (protocol in PROTOCOL.md).
Usage: python watch_act.py <pooled.csv> <IMS data dir> <out dir>"""
import sys, json, numpy as np
from scipy.stats import norm, wilcoxon, binomtest
from p3lib import load_failed, load_ims_nonfailed, rule, persist, cp_ci, BASE_END, RUNIN
POOLED, IMSD, OUT = sys.argv[1:4]
Cp, Cf, Cfa0, EL = 14500.0, 88000.0, 2500.0, 1053.2
AGE = {'1.5': 71227.37673442051, '2.0': 55859.9366910734, '3.0': 40241.562925333004}
RTF = 1000 * Cf / EL

def mk_p(x, w):
    """one-sided Mann-Kendall p-value for an upward trend over the trailing window of length w (nan before w points)"""
    n = len(x); p = np.full(n, np.nan)
    if n < w: return p
    W = np.lib.stride_tricks.sliding_window_view(x, w)            # (n-w+1, w)
    s = np.zeros(W.shape[0])
    for i in range(w - 1):
        s += np.sign(W[:, i + 1:] - W[:, [i]]).sum(axis=1)
    var = w * (w - 1) * (2 * w + 5) / 18.0
    z = np.where(s > 0, (s - 1) / np.sqrt(var), np.where(s < 0, (s + 1) / np.sqrt(var), 0.0))
    p[w - 1:] = 1 - norm.cdf(z)
    return p

CACHE = {}
def axis_feats(key, r, w):
    k = (key, w)
    if k not in CACHE: CACHE[k] = mk_p(np.log(np.maximum(r, 1e-9)), w)
    return CACHE[k]

def bearing_act(b, act, c_act=2.0, alpha=0.01, w=30, watch='M4'):
    n = len(b['t']); W = np.logical_or.reduce([rule(r, watch) for r in b['axes']])
    conds = []
    for j, r in enumerate(b['axes']):
        esc = persist(r > c_act, 3)
        if act in ('A2', 'A3', 'A4'):
            p = axis_feats((b['dataset'], b['unit'], j), r, w); tr = persist(np.nan_to_num(p, nan=1.0) < alpha, 3)
        if act == 'A0': c = np.ones(n, bool)
        elif act == 'A1': c = esc
        elif act == 'A2': c = tr
        elif act == 'A3': c = esc | tr
        elif act == 'A4': c = persist((r > c_act) & (np.nan_to_num(p, nan=1.0) < alpha), 3)
        conds.append(c)
    A = np.logical_or.reduce(conds) & W
    A[:BASE_END] = False
    return W, A

def score(b, W, A, lead=0.01):
    t, life, n = b['t'], b['life'], len(W)
    rise = np.where(W & ~np.r_[False, W[:-1]])[0]
    ia = np.where(A)[0]
    if len(ia):
        ta = t[ia[0]]; intime = bool(ta <= life * (1 - lead) + 1e-12)
        nins = int((rise < ia[0]).sum())   # WATCH episodes started before ACT; the episode containing ACT is part of replacement
        # the episode in which ACT fires started at or before ia[0]; count only episodes that ended before ACT
        cur = rise[rise <= ia[0]]
        if len(cur): nins = len(cur) - 1
        return dict(intime=intime, wasted=float((life - ta) / life) if intime else 0.0, t_act=float(ta / life), nins=nins if intime else len(rise))
    return dict(intime=False, wasted=0.0, t_act=None, nins=len(rise))

def cost(rows, cfa=Cfa0):
    num = sum((Cp if r['intime'] else Cf) + r['nins'] * cfa for r in rows)
    den = sum(EL * (1 - r['wasted'] * r['intime']) for r in rows)
    return 1000 * num / den

def summarize(rows, cfa=Cfa0):
    n = len(rows); k = sum(r['intime'] for r in rows); wl = [r['wasted'] for r in rows if r['intime']]
    return dict(n=n, intime=k, ci=cp_ci(k, n), median_wasted=float(np.median(wl)) if wl else None, mean_wasted=float(np.mean(wl)) if wl else None,
                inspections=int(sum(r['nins'] for r in rows)), cost=cost(rows, cfa))

def evaluate(B, act, lead=0.01, **kw):
    out = []
    for b in B:
        W, A = bearing_act(b, act, **kw); out.append(dict(dataset=b['dataset'], unit=b['unit'], **score(b, W, A, lead)))
    return out

B = load_failed(POOLED); NF = load_ims_nonfailed(IMSD)
print('failed', len(B), 'non-failed', len(NF), flush=True)
ACTS = ['A0', 'A1', 'A2', 'A3', 'A4']
R = dict(protocol='PROTOCOL.md', costs=dict(Cp=Cp, Cf=Cf, Cfa=Cfa0, EL=EL, age_opt=AGE, rtf=RTF))
main, rows_by = {}, {}
for a in ACTS:
    rows = evaluate(B, a); rows_by[a] = rows; s = summarize(rows)
    s['by_dataset'] = {ds: summarize([r for r in rows if r['dataset'] == ds]) for ds in ['IMS', 'XJTU-SY', 'FEMTO']}
    nf = []
    for b in NF:
        W, A = bearing_act(b, a); ia = np.where(A)[0]
        nf.append(dict(unit=b['unit'], act=bool(len(ia)), act_before_final=bool(len(ia) and b['t'][ia[0]] / b['life'] < 0.85),
                       t_act=float(b['t'][ia[0]] / b['life']) if len(ia) else None))
    s['nonfailed'] = dict(n=len(nf), acted=sum(x['act'] for x in nf), acted_before_final=sum(x['act_before_final'] for x in nf), units=nf)
    if a != 'A0':
        d0 = np.array([r['intime'] for r in rows_by['A0']]); d1 = np.array([r['intime'] for r in rows])
        lost, gained = int((d0 & ~d1).sum()), int((~d0 & d1).sum())
        s['mcnemar'] = dict(lost=lost, gained=gained, p=float(binomtest(lost, lost + gained).pvalue) if lost + gained else 1.0)
        both = d0 & d1; w0 = np.array([r['wasted'] for r in rows_by['A0']])[both]; w1 = np.array([r['wasted'] for r in rows])[both]
        s['wasted_paired'] = dict(n=int(both.sum()), median_A0=float(np.median(w0)) if both.any() else None, median_rule=float(np.median(w1)) if both.any() else None,
                                  p=float(wilcoxon(w0, w1).pvalue) if both.sum() > 1 and np.any(w0 != w1) else 1.0)
    s['units'] = rows; main[a] = s
    print(a, s['intime'], [round(x, 2) for x in s['ci']], s['median_wasted'], s['inspections'], round(s['cost']), s.get('mcnemar'), s.get('wasted_paired', {}).get('p'),
          'nonfailed', s['nonfailed']['acted'], s['nonfailed']['acted_before_final'], flush=True)
R['main'] = main

sens = {}
for lab, kw, lead, cfa in [('lead0.5pct', {}, 0.005, Cfa0), ('lead2pct', {}, 0.02, Cfa0), ('cfa1000', {}, 0.01, 1000.0), ('cfa5000', {}, 0.01, 5000.0), ('watchM0', dict(watch='M0'), 0.01, Cfa0)]:
    sens[lab] = {a: summarize(evaluate(B, a, lead=lead, **kw), cfa) for a in ACTS}
    print(lab, {a: (v['intime'], round(v['cost'])) for a, v in sens[lab].items()}, flush=True)
R['sensitivity'] = sens

CG = [1.5 + 0.25 * i for i in range(11)]; AG = [0.001, 0.01, 0.05]; WG = [20, 30, 50]
grid = [('A0', {})] + [('A1', dict(c_act=c)) for c in CG] + [('A2', dict(alpha=al, w=w)) for al in AG for w in WG]
grid += [(a, dict(c_act=c, alpha=al, w=w)) for a in ('A3', 'A4') for c in CG for al in AG for w in WG]
G = [dict(act=a, kw=kw, rows=evaluate(B, a, **kw)) for a, kw in grid]
print('grid', len(G), flush=True)
DS = ['IMS', 'XJTU-SY', 'FEMTO']
def sub(rows, dss): return [r for r in rows if r['dataset'] in dss]
lodo = {}
for hold in DS:
    tr = [d for d in DS if d != hold]; best = min(G, key=lambda g: cost(sub(g['rows'], tr)))
    lodo[hold] = dict(act=best['act'], kw=best['kw'], train_cost=cost(sub(best['rows'], tr)), test=summarize(sub(best['rows'], [hold])),
                      test_defaults={a: summarize(sub(rows_by[a], [hold])) for a in ACTS})
R['lodo'] = lodo
R['grid_summary'] = [dict(act=g['act'], **g['kw'], **{k: v for k, v in summarize(g['rows']).items() if k != 'ci'}) for g in G]
best_in = {a: min([g for g in G if g['act'] == a], key=lambda g: cost(g['rows'])) for a in ACTS}
R['best_in_sample'] = {a: dict(kw=g['kw'], **summarize(g['rows'])) for a, g in best_in.items()}
json.dump(R, open(f'{OUT}/paper4.json', 'w'), indent=1, default=float)
print('LODO', json.dumps({h: (v['act'], v['kw'], v['test']['intime'], v['test']['n'], round(v['test']['cost']), {a: (x['intime'], round(x['cost'])) for a, x in v['test_defaults'].items()}) for h, v in lodo.items()}))
print('best in-sample', json.dumps({a: (v['kw'], v['intime'], round(v['cost']), v['median_wasted']) for a, v in R['best_in_sample'].items()}))
