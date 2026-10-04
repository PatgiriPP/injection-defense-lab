#!/usr/bin/env bash
# Launch the agent lab in Omnigent with the provider/model from .env
#   bash scripts/start_lab.sh            -> interactive (you can approve ASK prompts)
#   bash scripts/start_lab.sh "prompt"   -> one-shot
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
case "${LAB_PROVIDER:-gemini}" in
  gemini)     export OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai OPENAI_API_KEY="$GEMINI_API_KEY" ;;
  openrouter) export OPENAI_BASE_URL=https://openrouter.ai/api/v1 OPENAI_API_KEY="$OPENROUTER_API_KEY" ;;
  groq)       export OPENAI_BASE_URL=https://api.groq.com/openai/v1 OPENAI_API_KEY="$GROQ_API_KEY" ;;
  openai)     unset OPENAI_BASE_URL ;;
  *) echo "Unknown LAB_PROVIDER=$LAB_PROVIDER"; exit 1 ;;
esac
python scripts/set_model.py "${LAB_MODEL:?set LAB_MODEL in .env}" >/dev/null
omnigent stop >/dev/null 2>&1 || true   # restart so the server picks up the keys
echo "Agents: $LAB_PROVIDER / $LAB_MODEL   |   Target: $TARGET_PROVIDER / $TARGET_MODEL"
if [ $# -gt 0 ]; then
  omnigent run lab -p "$1"
else
  omnigent run lab
fi
