# Paper 3 analysis protocol: reducing nuisance alarms without labels
Fixed 2026-10-14, before any paper 3 result was computed. Paper 2 results (same 33 bearings) were already known; this is stated in the paper.

## Data
The 33 evaluable failed bearings of paper 2 (IMS 4, XJTU-SY 12, FEMTO 17), same features, clocks, run-in (snapshots 1-10) and baseline (11-60).
Specificity control: the 8 non-failed IMS bearings (Test 1 B1, B2 with x and y; Test 2 B2-B4; Test 3 B1, B2, B4; 10 channels), processed identically.

## Bearing-level alarm signal
All rules produce a per-axis boolean; the bearing signal is the OR over axes (except M5). All rules use k = 3 consecutive raw exceedances unless stated.

## Outcomes (all label-free)
- Detection: sustained bearing alarm (block reaching the end of record, gaps <= 1% of life) of at least 1% of life. k/33 with Clopper-Pearson 95% CI.
- Primary nuisance outcome: **nuisance episodes** = alarm episodes of the bearing signal that end before the end of the record (an alarm that clears on its own was not followed by failure while on). Reported as mean per bearing and number of bearings with >= 1.
- Secondary: paper 2 healthy-zone false-alarm episodes (snapshot 61 to 85% of life); first-alarm time as a fraction of life; sustained warning as a fraction of life.
- Non-failed IMS bearings: nuisance episodes and bearings with any alarm before the final 15% of the run.

## Methods (defaults fixed now)
- M0 reference: RMS ratio r_t = RMS_t / mu_0 > 1.2, k = 3.
- M1 m-of-n: alarm when >= 8 of the last 10 snapshots have r > 1.2.
- M2 causal median: rolling median of r over the last 10 snapshots > 1.2, k = 3.
- M3 EWMA: z_t = 0.1 r_t + 0.9 z_{t-1} (z = 1 at the end of baseline) > 1.2, k = 3.
- M4 hysteresis: switch on after k = 3 snapshots with r > 1.2; switch off only after k = 3 snapshots with r < 1.1.
- M5 axis vote: M0 per axis, bearing alarm only when all axes alarm (single-axis bearings unchanged).
- M6 combined: M2 median filter followed by M4 hysteresis.
- M7 CUSUM on log ratio: S_t = max(0, S_{t-1} + ln r_t - ln 1.1), alarm when S_t > 5 ln 1.2.

## Paired statistics vs M0
Nuisance episodes per bearing: Wilcoxon signed-rank (two-sided). Detection: exact McNemar. No multiplicity correction; 7 comparisons reported in full.

## Empirical cost (renewal-reward over the 33 bearings)
Costs as papers 1-2: Cp = 14,500, Cf = 88,000, Cfa = 2,500 USD; lives scaled to E[L] = 1,053.2 h by fraction of life.
g = sum_i [d_i Cp + (1-d_i) Cf + N_i Cfa] / sum_i E[L] (1 - d_i w_i), where N_i = nuisance episodes, and w_i (wasted life) is
- pessimistic: the sustained warning fraction (replace when the sustained alarm starts),
- optimistic: 0.01 (replace just in time once warned).
Compared with run-to-failure and optimal age replacement (Weibull beta 1.5 / 2 / 3, same mean).

## Leave-one-dataset-out selection
Grid: c_on in {1.10, 1.15, ..., 2.00} for every method, plus m in {6, 8, 10} (M1), window in {5, 10, 20} (M2), lambda in {0.05, 0.1, 0.2} (M3),
c_off / c_on in {0.85, 0.90, 0.95} (M4, M6; M6 window 10), H in {3, 5, 10} x ln 1.2 (M7; reference ln 1.1 scaled as ln(c_on) - ln 1.2 + ln 1.1).
On two datasets choose the configuration (method + parameters) with the lowest pessimistic empirical cost; report detection, nuisance and cost on the held-out dataset. Also report the best configuration per method.

## Sensitivity
k = 5; detection threshold 2% of life; costs Cfa = 1,000 and 5,000.

## Amendment log
- 2026-10-14, after the first run: the non-failed control was miscounted as 10 bearings (it is 8 bearings, 10 channels). A coding error that counted only episodes before the gap-merged sustained block as nuisance was corrected to the definition above (every episode that ends before the end of the record). No rule, parameter or outcome definition was changed.
