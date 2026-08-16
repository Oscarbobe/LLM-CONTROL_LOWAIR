#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip install -r requirements.txt
python -m pip install pytest

if command -v ollama >/dev/null 2>&1; then
  ollama pull qwen3.5:4b
else
  echo "未检测到 ollama，请先安装 Ollama 后再执行：ollama pull qwen3.5:4b"
fi
