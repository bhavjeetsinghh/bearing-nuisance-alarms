"""Figures for paper 3. Usage: python figs3.py <pooled.csv> <paper3.json> <out dir>"""
import sys, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from p3lib import load_failed, rule, bearing_signal
POOLED, RJ, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
R = json.load(open(RJ)); B = load_failed(POOLED)
BLUE, ORANGE, AQUA, INK, MUTED, GRID = '#2a78d6', '#eb6834', '#1baf7a', '#222222', '#6b6b6b', '#e4e4e0'
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 8, 'axes.titlesize': 8,
                     'axes.labelsize': 8, 'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7, 'axes.edgecolor': MUTED,
                     'axes.linewidth': 0.6, 'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.grid': True, 'grid.color': GRID,
                     'grid.linewidth': 0.5, 'savefig.dpi': 600, 'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False})
W1, W2 = 3.4, 7.0
def save(fig, name): fig.savefig(f'{OUT}/{name}.png', bbox_inches='tight'); fig.savefig(f'{OUT}/{name}.pdf', bbox_inches='tight'); plt.close(fig)

# Fig 1: example bearing, ratio and bearing-level alarm signal of M0, M4, M7
b = next(x for x in B if x['unit'] == 'Bearing3_2' and x['dataset'] == 'XJTU-SY')
f = b['t'] / b['life']
fig = plt.figure(figsize=(W2, 2.9)); gs = GridSpec(4, 1, height_ratios=[3.2, 0.45, 0.45, 0.45], hspace=0.25)
ax = fig.add_subplot(gs[0])
for r, lab, col in zip(b['axes'], ['horizontal', 'vertical'], [BLUE, AQUA]): ax.plot(f, r, lw=0.5, color=col, alpha=0.8, label=lab)
ax.axhline(1.2, color=INK, ls=':', lw=0.7, label='switch on (1.2×)'); ax.axhline(1.1, color=INK, ls='--', lw=0.6, label='M4 switch off (1.1×)')
ax.set_yscale('log'); ax.set_ylim(0.6, 15); ax.set_yticks([0.7, 1, 1.5, 2, 5, 10]); ax.set_yticklabels(['0.7', '1', '1.5', '2', '5', '10']); ax.minorticks_off()
ax.set_xlim(0, 1); plt.setp(ax.get_xticklabels(), visible=False); ax.set_ylabel('RMS / baseline mean'); ax.legend(loc='upper left', ncol=2)
ax.set_title('XJTU-SY Bearing 3_2 (2,496 snapshots)', loc='left')
for i, (m, lab) in enumerate([('M0', 'M0 reference'), ('M4', 'M4 hysteresis'), ('M7', 'M7 CUSUM')]):
    a = bearing_signal(b, m); s = fig.add_subplot(gs[i + 1], sharex=ax)
    s.fill_between(f, 0, a.astype(float), step='post', color=ORANGE if m == 'M0' else BLUE, lw=0)
    nu = int((a & ~np.r_[False, a[:-1]]).sum()) - int(a[-1])
    s.set_yticks([]); s.set_ylim(0, 1); s.grid(False); s.spines['left'].set_visible(False)
    s.text(-0.01, 0.5, lab, ha='right', va='center', fontsize=7, transform=s.transAxes)
    s.text(1.01, 0.5, f'{nu} nuisance', ha='left', va='center', fontsize=7, color=MUTED, transform=s.transAxes)
    if i < 2: plt.setp(s.get_xticklabels(), visible=False)
s.set_xlabel('Fraction of life')
save(fig, 'fig1_example')

# Fig 2: detection vs nuisance episodes, all grid configurations and defaults
g = pd.DataFrame(R['grid_summary']); M = R['main']
fig, ax = plt.subplots(figsize=(W1, 2.6))
ax.scatter(g.nuis_total + 1, g.detected + (np.random.default_rng(2).random(len(g)) - 0.5) * 0.3, s=5, color='#bdbdb8', lw=0, label='grid configurations')
off = {'M0': (4, 3), 'M1': (4, -7), 'M2': (4, 3), 'M3': (4, 3), 'M4': (4, 3), 'M5': (-12, -8), 'M6': (-14, -8), 'M7': (-14, 3)}
for m, s in M.items():
    col = ORANGE if m == 'M0' else (BLUE if m in ('M4', 'M7') else INK)
    ax.scatter(s['nuis_total'] + 1, s['detected'], s=22, color=col, zorder=3)
    ax.annotate(m, (s['nuis_total'] + 1, s['detected']), xytext=off[m], textcoords='offset points', fontsize=7, color=col)
ax.set_xscale('log'); ax.set_xlabel('Nuisance alarm episodes, 33 bearings (+1, log)'); ax.set_ylabel('Failures detected (of 33)')
ax.set_ylim(18, 34); ax.legend(loc='lower right')
save(fig, 'fig2_tradeoff')

# Fig 3: empirical cost of default rules
order = ['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7']
fig, ax = plt.subplots(figsize=(W1, 2.4))
x = np.arange(len(order)); pe = [M[m]['cost_pess'] / 1000 for m in order]; op = [M[m]['cost_opt'] / 1000 for m in order]
ax.bar(x, pe, width=0.6, color=[ORANGE if m == 'M0' else (BLUE if m in ('M4', 'M7') else '#9a9a95') for m in order], label='replace at warning')
ax.scatter(x, op, marker='_', s=120, color=INK, zorder=3, label='replace just in time')
for lab, v, ls in [('age replacement, β = 2', R['costs']['age_opt']['2.0'], '--'), ('age replacement, β = 3', R['costs']['age_opt']['3.0'], ':')]:
    ax.axhline(v / 1000, color=MUTED, ls=ls, lw=0.8); ax.text(7.45, v / 1000 + 0.8, lab, fontsize=6.5, color=MUTED, ha='right')
ax.set_xticks(x); ax.set_xticklabels(order); ax.set_ylabel('Cost (thousand USD per 1,000 h)'); ax.set_ylim(0, 60); ax.grid(axis='x', visible=False)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(color='#9a9a95', label='replace when warning starts'), Line2D([], [], color=INK, lw=2.5, label='replace just in time')], loc='upper left', ncol=2, bbox_to_anchor=(0, 1.13))
save(fig, 'fig3_cost')
print('ok')
