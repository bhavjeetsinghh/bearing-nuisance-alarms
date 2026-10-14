# Secondary analysis protocol: when to replace after an alarm (watch-and-act rules)
Fixed 2026-10-14 after the main nuisance-alarm results were known and before this analysis was run (reported as a secondary analysis, Section 3.6 of the paper).

## Question
The main analysis and the pooled study scored replacement at the start of the sustained warning, a time known only in hindsight. A real policy must decide causally when to replace.
Here an alarm opens a WATCH state (inspect, keep running); a separate ACT rule, evaluated only while WATCH is on, triggers replacement.
ACT latches: replacement happens at the first ACT snapshot.

## Data
The 33 evaluable failed bearings (IMS 4, XJTU-SY 12, FEMTO 17) and the 8 non-failed IMS bearings of the main analysis; same features, clocks, run-in (1-10) and baseline (11-60).

## WATCH
M4 hysteresis of the main analysis on the RMS ratio r_t = RMS_t / mu_0: on after 3 snapshots with r > 1.2, off after 3 snapshots with r < 1.1; bearing WATCH = OR over axes.

## ACT rules (latching; axis-level condition, bearing ACT = OR over axes, only while bearing WATCH is on)
- A0 immediate: ACT at the first WATCH snapshot.
- A1 escalation: r > 2.0 for 3 consecutive snapshots.
- A2 trend confidence: one-sided Mann-Kendall test of an upward trend in ln r over the last 30 snapshots, p < 0.01, for 3 consecutive snapshots.
- A3 escalation OR trend: A1 or A2.
- A4 escalation AND trend: A1 and A2 at the same snapshot, 3 consecutive snapshots.

## Outcomes per failed bearing
- In-time replacement: ACT at or before (end of record - 1% of life) (minimum planning lead). Otherwise (late or never) the bearing fails.
- Wasted life: (life - t_ACT) / life for in-time replacements.
- Inspections: WATCH episodes that start before t_ACT (for failures: all WATCH episodes); the episode during which ACT fires is included in the replacement cost.
Primary: in-time replacements k/33 (Clopper-Pearson 95% CI); median wasted life; empirical cost.
Non-failed IMS bearings: number of bearings with any ACT (unnecessary replacement) and ACTs before the final 15% of the run.

## Empirical cost (renewal-reward over the 33 bearings, as in the main analysis)
Cp = 14,500, Cf = 88,000, Cfa = 2,500 USD per inspection; lives scaled to E[L] = 1,053.2 h.
g = sum_i [I_i Cp + (1 - I_i) Cf + N_i Cfa] / sum_i E[L](1 - I_i w_i). Compared with run-to-failure and optimal age replacement (Weibull beta 1.5/2/3).

## Paired statistics vs A0
In-time replacement: exact McNemar. Wasted life among bearings replaced in time under both rules: Wilcoxon signed-rank. 4 comparisons, no correction.

## Grid and leave-one-dataset-out selection
A1: c_act in {1.50, 1.75, ..., 4.00}. A2: alpha in {0.001, 0.01, 0.05} x window in {20, 30, 50}. A3, A4: the A1 grid crossed with the A2 grid.
On two datasets choose the configuration with the lowest empirical cost; report it on the held-out dataset.

## Sensitivity
Planning lead 0.5% and 2% of life; Cfa = 1,000 and 5,000; WATCH = the reference rule M0 (no hysteresis).
