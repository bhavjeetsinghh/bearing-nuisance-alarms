#!/usr/bin/env bash
# Reproduces every number, table and figure of the paper from the feature tables in data/ (about 30 s).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results figures
python src/unify.py data results/pooled.csv
(cd src && python nuisance.py ../results/pooled.csv ../data ../results)
(cd src && python figs3.py ../results/pooled.csv ../results/paper3.json ../figures)
echo "Done: results/paper3.json and figures/"
