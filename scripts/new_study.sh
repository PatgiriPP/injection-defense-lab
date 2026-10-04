#!/usr/bin/env bash
# Start a fresh agent study: archives the research log + budget ledger.
# The sample cache is KEPT (cached samples are free and identical).
set -euo pipefail
cd "$(dirname "$0")/../results"
stamp=$(date +%Y%m%d-%H%M%S)
mkdir -p archive
for f in research_log.jsonl budget_ledger.json; do [ -f "$f" ] && mv "$f" "archive/${stamp}-$f"; done
echo "Fresh study ready (old log archived to results/archive/)."
