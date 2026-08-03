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
RUN_WITH_SUDO="${RUN_WITH_SUDO:-1}"
SKIP_BLUETOOTH_FIX="${SKIP_BLUETOOTH_FIX:-0}"
BLUETOOTH_DEVICE="${BLUETOOTH_DEVICE:-0489:e111}"
UPDATE_BLUETOOTH_FIRMWARE="${UPDATE_BLUETOOTH_FIRMWARE:-0}"
INSTALL_BLUETOOTH_FIX="${INSTALL_BLUETOOTH_FIX:-0}"
RETRY_BLUETOOTH_RECOVERY="${RETRY_BLUETOOTH_RECOVERY:-1}"
DEFAULT_ACTION_FILE="$PROJECT_DIR/data/processed/instructions/demo_actions.json"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
  log "ERROR: $*"
  exit 1
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
Usage: $(basename "$0") --addr MAC [--file actions.json | --json JSON] [--no-sudo] [--skip-bluetooth-fix] [--bluetooth-device VID:PID] [--update-bluetooth-firmware] [--install-bluetooth-fix]

Examples:
  $(basename "$0") --addr E0:14:89:09:3D:CB
  $(basename "$0") --addr E0:14:89:09:3D:CB --file data/processed/instructions/demo_actions.json

Environment:
  PYTHON_BIN=/path/to/python       Python with pyparrot installed
  RUN_WITH_SUDO=0                  Run BLE commands without sudo
  FIX_SCRIPT=/path/to/script.sh    Optional Bluetooth repair script
  BLUETOOTH_DEVICE=0489:e111       USB Bluetooth VID:PID for MT7925 recovery
EOF
}

main() {
  local addr=""
  local action_args=()

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --addr)
        [ "$#" -ge 2 ] || die "--addr requires a MAC address"
        addr="$2"
        shift 2
        ;;
      --file)
        [ "$#" -ge 2 ] || die "--file requires a JSON file"
        action_args=(--file "$2")
        shift 2
        ;;
      --json)
        [ "$#" -ge 2 ] || die "--json requires a JSON string"
        action_args=(--json "$2")
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
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done

  [ -n "$addr" ] || die "Missing --addr MAC"
  [ -x "$PYTHON_BIN" ] || die "Python not found: $PYTHON_BIN"
  "$PYTHON_BIN" -c "from pyparrot.Minidrone import Swing" >/dev/null || die "pyparrot is not importable with $PYTHON_BIN"

  if [ "${#action_args[@]}" -eq 0 ]; then
    action_args=(--file "$DEFAULT_ACTION_FILE")
  fi

  cd "$PROJECT_DIR" || die "Cannot enter $PROJECT_DIR"

  log "Step 1/4: preparing Bluetooth."
  prepare_bluetooth_controller || die "Bluetooth recovery failed."

  log "Step 2/4: validating actions and showing dry-run preview."
  log "Step 3/4: waiting for manual confirmation in Python entrypoint."
  log "Step 4/4: executing with pyparrot after confirmation."

  run_privileged env PYTHONPATH="$PROJECT_DIR/src" "$PYTHON_BIN" \
    -m swing_control.app.execute_actions \
    --addr "$addr" \
    "${action_args[@]}"
}

main "$@"
