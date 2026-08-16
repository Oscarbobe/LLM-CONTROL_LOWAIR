#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

find_port() {
  local start_port="${1:-8501}"
  python - "$start_port" <<'PY'
import socket
import sys

start = int(sys.argv[1])
for port in range(start, start + 20):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", port)) != 0:
            print(port)
            raise SystemExit(0)
raise SystemExit(1)
PY
}

REQUESTED_PORT="${STREAMLIT_PORT:-8501}"
PORT="$(find_port "$REQUESTED_PORT")"
if [[ "$PORT" != "$REQUESTED_PORT" ]]; then
  echo "端口 $REQUESTED_PORT 已被占用，自动改用 $PORT。"
fi
echo "Streamlit 功能展示面板：http://127.0.0.1:$PORT"

PYTHONPATH=src STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run demo_streamlit.py \
  --server.address 127.0.0.1 \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false
