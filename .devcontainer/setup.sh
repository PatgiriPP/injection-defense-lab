#!/usr/bin/env bash
set -e
sudo apt-get update -y && sudo apt-get install -y tmux bubblewrap
pip install --upgrade pip
pip install omnigent
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[detector]"
[ -f .env ] || cp .env.example .env
echo "Setup done. Edit .env, then: python scripts/check_setup.py"
