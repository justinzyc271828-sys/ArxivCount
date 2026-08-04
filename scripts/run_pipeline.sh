#!/usr/bin/env bash
# ArxivCount end-to-end pipeline
set -euo pipefail
cd "$(dirname "$0")/.."

MAX_PER_QUERY="${1:-}"

if [[ -n "$MAX_PER_QUERY" ]]; then
  python -m src.collect --max-per-query "$MAX_PER_QUERY"
else
  python -m src.collect
fi

python -m src.aggregate
python -m src.curate --min-level L1

echo "Done. Launch dashboard with: streamlit run app.py"
