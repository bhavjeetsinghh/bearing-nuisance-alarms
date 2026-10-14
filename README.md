# Reducing nuisance alarms of bearing early-warning rules

Code and data for the paper *Hysteresis, Not Filtering: Reducing Nuisance Alarms of Label-Free Bearing Early-Warning Rules Across Three Run-to-Failure Datasets* (Bhavjeet Singh Hora, Florida International University).

Seven standard alarm-processing methods (m-of-n vote, median filter, EWMA, hysteresis, axis voting, median + hysteresis, CUSUM) are compared with an RMS ratio rule (1.2× an early-life baseline) on the 33 evaluable run-to-failure bearings of NASA IMS, XJTU-SY and FEMTO/PRONOSTIA, plus 8 non-failed IMS bearings. A nuisance alarm is any alarm episode that switches off before the end of the record, so no degradation labels are needed.

**Main result:** hysteresis (switch on at 1.2×, off below 1.1×) cuts nuisance alarms from 144 to 36, misses no additional failure (32/33) and lowers an illustrative renewal-reward maintenance cost by about 30%.

Companion repositories: [ims-bearing-label-free-early-warning](https://github.com/bhavjeetsinghh/ims-bearing-label-free-early-warning) (IMS study) and [bearing-early-warning-transfer](https://github.com/bhavjeetsinghh/bearing-early-warning-transfer) (pooled study).

## Protocol fixed in advance
[`PROTOCOL.md`](PROTOCOL.md) lists every rule default, outcome and test, written before any result was computed, with an amendment log.

## Reproduce
```bash
pip install numpy pandas scipy matplotlib
bash run_all.sh
```
Outputs: `results/paper3.json` (all reported numbers) and `figures/fig1–3` (PNG and PDF).

## Files
- `data/` — per-snapshot features from the pooled study (IMS `test1–3.csv`, `xjtu_features.csv`, `femto_features.csv`)
- `src/unify.py`, `src/extract_runs.py` — from the pooled study (common table; raw-data feature extraction)
- `src/p3lib.py` — alarm rules M0–M7, scoring, empirical cost
- `src/nuisance.py` — main analysis, paired tests, sensitivity, leave-one-dataset-out selection
- `src/figs3.py` — figures

## License
MIT. The original datasets remain under their providers' terms.
