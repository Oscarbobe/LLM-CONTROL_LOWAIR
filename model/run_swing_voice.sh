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
SWING_LLM_MODEL="${SWING_LLM_MODEL:-qwen3.5:4b}"
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

run_privileged() {
  if [ "$RUN_WITH_SUDO" = "0" ] || [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_connection_test() {
  local addr="$1"
  local output_file
  output_file="$(mktemp /tmp/swing_voice_connection.XXXXXX)"

  log "Running connection-only test before voice execution."
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

# shellcheck source=/dev/null
[ -f "$BLUETOOTH_COMMON" ] || die "Bluetooth common script not found: $BLUETOOTH_COMMON"
source "$BLUETOOTH_COMMON"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--check-env] [--execute] [--addr MAC] [--model MODEL] [--record-seconds N] [--asr-model MODEL] [--no-sudo] [--skip-bluetooth-fix]

Examples:
  $(basename "$0") --check-env
  $(basename "$0")
  $(basename "$0") --record-seconds 5
  $(basename "$0") --execute --addr E0:14:89:09:3D:CB

Voice flow:
  press Enter -> record microphone -> Whisper ASR -> Chinese instruction parser -> preview -> confirm -> pyparrot
EOF
}

main() {
  local execute=0
  local addr_in_args=0
  local swing_addr="$SWING_ADDR"
  local passthrough=()

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --execute)
        execute=1
        passthrough+=("$1")
        shift
        ;;
      --no-sudo)
        RUN_WITH_SUDO=0
        shift
        ;;
      --addr)
        [ "$#" -ge 2 ] || die "--addr requires a MAC address"
        swing_addr="$2"
        addr_in_args=1
        passthrough+=("$1" "$2")
        shift 2
        ;;
      --model)
        [ "$#" -ge 2 ] || die "--model requires a model name"
        SWING_LLM_MODEL="$2"
        passthrough+=("$1" "$2")
        shift 2
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
      --record-seconds|--audio-dir|--audio-device|--sample-rate|--asr-backend|--asr-model|--asr-language|--save-actions|--log-dir|--retries)
        [ "$#" -ge 2 ] || die "$1 requires a value"
        passthrough+=("$1" "$2")
        shift 2
        ;;
      --no-log)
        passthrough+=("$1")
        shift
        ;;
      --check-env)
        passthrough+=("$1")
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

  [ -x "$PYTHON_BIN" ] || die "Python not found: $PYTHON_BIN"
  command -v ollama >/dev/null 2>&1 || die "ollama command not found"

  cd "$PROJECT_DIR" || die "Cannot enter $PROJECT_DIR"

  if [ "$execute" = "1" ]; then
    [ -f "$FLIGHT_DEMO" ] || die "Flight demo not found: $FLIGHT_DEMO"
    "$PYTHON_BIN" -c "from pyparrot.Minidrone import Swing" >/dev/null || die "pyparrot is not importable with $PYTHON_BIN"

    log "Preparing Bluetooth for voice real execution."
    prepare_bluetooth_controller || die "Bluetooth recovery failed."

    if [ -n "$swing_addr" ]; then
      log "Using Swing address from --addr or SWING_ADDR: $swing_addr"
    else
      log "Scanning Swing address for voice execution."
      swing_addr="$(find_swing_addr_with_recovery || true)"
      [ -n "$swing_addr" ] || die "Could not find a Swing device. Turn on Swing, keep it nearby, and retry."
      log "Found Swing address: $swing_addr"
    fi

    run_connection_test "$swing_addr" || die "Connection test failed. Voice execution was not started."

    if [ "$addr_in_args" = "0" ]; then
      passthrough+=("--addr" "$swing_addr")
    fi

    run_privileged env \
      HOME="${HOME:-}" \
      XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" \
      PULSE_SERVER="${PULSE_SERVER:-}" \
      PYTHONPATH="$PROJECT_DIR/src" \
      SWING_LLM_MODEL="$SWING_LLM_MODEL" \
      "$PYTHON_BIN" \
      -m swing_control.app.voice_control \
      "${passthrough[@]}"
  else
    env PYTHONPATH="$PROJECT_DIR/src" SWING_LLM_MODEL="$SWING_LLM_MODEL" "$PYTHON_BIN" \
      -m swing_control.app.voice_control \
      "${passthrough[@]}"
  fi
}

main "$@"
