#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "/home/abc/miniconda3/bin/python" ]; then
    PYTHON_BIN="/home/abc/miniconda3/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  fi
fi

FIX_SCRIPT="${FIX_SCRIPT:-$SCRIPT_DIR/fix_mt7925_bluetooth.sh}"
BLUETOOTH_COMMON="$SCRIPT_DIR/swing_bluetooth_common.sh"
FLIGHT_DEMO="$SCRIPT_DIR/demoSwingDirectFlight.py"
RUN_WITH_SUDO="${RUN_WITH_SUDO:-1}"
SKIP_BLUETOOTH_FIX="${SKIP_BLUETOOTH_FIX:-0}"
SWING_ADDR="${SWING_ADDR:-}"
BLUETOOTH_DEVICE="${BLUETOOTH_DEVICE:-0489:e111}"
UPDATE_BLUETOOTH_FIRMWARE="${UPDATE_BLUETOOTH_FIRMWARE:-0}"
INSTALL_BLUETOOTH_FIX="${INSTALL_BLUETOOTH_FIX:-0}"
RETRY_BLUETOOTH_RECOVERY="${RETRY_BLUETOOTH_RECOVERY:-1}"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
  log "ERROR: $*"
  exit 1
}

write_swing_addr() {
  local addr="$1"

  log "Writing Swing address $addr into local demo."
  "$PYTHON_BIN" - "$addr" "$FLIGHT_DEMO" <<'PY'
import re
import sys
from pathlib import Path

addr = sys.argv[1]
paths = [Path(p) for p in sys.argv[2:]]

patterns = [
    re.compile(r'^(DEFAULT_SWING_ADDR\s*=\s*)["\'][^"\']*["\']', re.MULTILINE),
    re.compile(r'^(swingAddr\s*=\s*)["\'][^"\']*["\']', re.MULTILINE),
]

for path in paths:
    text = path.read_text()
    updated = text
    count = 0
    for pattern in patterns:
        updated, count = pattern.subn(rf'\1"{addr}"', updated, count=1)
        if count == 1:
            break
    if count != 1:
        raise SystemExit(f"Could not find a Swing address assignment in {path}")
    path.write_text(updated)
    print(f"updated {path}")
PY
}

run_connection_test() {
  local addr="$1"
  local output_file
  output_file="$(mktemp /tmp/swing_connection_test.XXXXXX)"

  log "Running connection-only test."
  run_privileged "$PYTHON_BIN" "$FLIGHT_DEMO" --addr "$addr" --connect-only 2>&1 | tee "$output_file"

  if grep -q "connected: True" "$output_file"; then
    rm -f "$output_file"
    log "Connection test passed."
    return 0
  fi

  log "Connection test did not report connected: True."
  log "Saved output: $output_file"
  return 1
}

run_privileged() {
  if [ "$RUN_WITH_SUDO" = "0" ] || [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

# shellcheck source=/dev/null
[ -f "$BLUETOOTH_COMMON" ] || die "Bluetooth common script not found: $BLUETOOTH_COMMON"
source "$BLUETOOTH_COMMON"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--addr MAC] [--no-sudo] [--skip-bluetooth-fix] [--bluetooth-device VID:PID] [--update-bluetooth-firmware] [--install-bluetooth-fix] [--no-bluetooth-retry]

Environment:
  PYTHON_BIN=/path/to/python       Python with pyparrot installed
  SWING_ADDR=E0:14:89:09:3D:CB     Skip scanning and use this Swing address
  RUN_WITH_SUDO=0                  Run BLE commands without sudo
  FIX_SCRIPT=/path/to/script.sh    Optional Bluetooth repair script
  BLUETOOTH_DEVICE=0489:e111       USB Bluetooth VID:PID for MT7925 recovery
EOF
}

main() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --addr)
        [ "$#" -ge 2 ] || die "--addr requires a MAC address"
        SWING_ADDR="$2"
        shift 2
        ;;
      --no-sudo)
        RUN_WITH_SUDO=0
        shift
        ;;
      --skip-bluetooth-fix)
        SKIP_BLUETOOTH_FIX=1
        shift
        ;;
      --bluetooth-device)
        [ "$#" -ge 2 ] || die "--bluetooth-device requires VID:PID"
        BLUETOOTH_DEVICE="$2"
        shift 2
        ;;
      --update-bluetooth-firmware)
        UPDATE_BLUETOOTH_FIRMWARE=1
        shift
        ;;
      --install-bluetooth-fix)
        INSTALL_BLUETOOTH_FIX=1
        shift
        ;;
      --no-bluetooth-retry)
        RETRY_BLUETOOTH_RECOVERY=0
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done

  cd "$PROJECT_DIR" || die "Cannot enter $PROJECT_DIR"

  [ -x "$PYTHON_BIN" ] || die "Python not found: $PYTHON_BIN"
  [ -f "$FLIGHT_DEMO" ] || die "Flight demo not found: $FLIGHT_DEMO"
  "$PYTHON_BIN" -c "from pyparrot.Minidrone import Swing" >/dev/null || die "pyparrot is not importable with $PYTHON_BIN"

  log "Step 1/5: enabling Bluetooth."
  prepare_bluetooth_controller || die "Bluetooth recovery failed. Do not continue to flight."

  if [ -n "$SWING_ADDR" ]; then
    swing_addr="$SWING_ADDR"
    log "Step 2/5: using Swing address from argument or environment."
  else
    log "Step 2/5: scanning Swing address."
    swing_addr="$(find_swing_addr_with_recovery || true)"
    if [ -z "$swing_addr" ]; then
      die "Could not find a Swing device. Turn on Swing, keep it nearby, and retry."
    fi
  fi

  log "Found Swing address: $swing_addr"

  log "Step 3/5: writing Swing address."
  write_swing_addr "$swing_addr"

  log "Step 4/5: testing connection."
  run_connection_test "$swing_addr" || die "Connection test failed. Flight demo was not started."

  log "Step 5/5: ready to run flight demo."
  printf '\n确认 Swing 在空旷安全区域，准备起飞后按 Enter；输入 q 后回车取消：'
  read -r answer
  if [ "$answer" = "q" ] || [ "$answer" = "Q" ]; then
    log "Canceled before flight."
    exit 0
  fi

  log "Starting flight demo."
  run_privileged "$PYTHON_BIN" "$FLIGHT_DEMO" --addr "$swing_addr"
}

main "$@"
