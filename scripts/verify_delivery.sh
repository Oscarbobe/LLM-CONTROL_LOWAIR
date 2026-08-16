#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Ubuntu environment check"
PYTHONPATH=src python -m swing_control.app.check_ubuntu_env

echo "[2/5] Unit tests"
PYTHONPATH=src python -m pytest -q

echo "[3/5] Text dry-run"
PYTHONPATH=src python -m swing_control.app.parse_instruction "起飞后悬停2秒再降落" --dry-run --no-log

echo "[4/5] Map planning"
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json

echo "[5/5] Delivery report"
PYTHONPATH=src python -m swing_control.app.generate_report \
  --instruction "飞到果园上方悬停两秒再降落" \
  --output data/reports/latest_report.md

echo "Ubuntu delivery verification completed."
