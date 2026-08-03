#!/usr/bin/env bash

BLUETOOTH_DEVICE="${BLUETOOTH_DEVICE:-0489:e111}"
UPDATE_BLUETOOTH_FIRMWARE="${UPDATE_BLUETOOTH_FIRMWARE:-0}"
INSTALL_BLUETOOTH_FIX="${INSTALL_BLUETOOTH_FIX:-0}"
RETRY_BLUETOOTH_RECOVERY="${RETRY_BLUETOOTH_RECOVERY:-1}"

bluetooth_fix_args() {
  [ -n "$BLUETOOTH_DEVICE" ] && printf '%s\0%s\0' --device "$BLUETOOTH_DEVICE"
  [ "$UPDATE_BLUETOOTH_FIRMWARE" = "1" ] && printf '%s\0' --update-firmware
  [ "$INSTALL_BLUETOOTH_FIX" = "1" ] && printf '%s\0' --install-persistent
}

bluetooth_controller_usable() {
  ls /sys/class/bluetooth/hci* >/dev/null 2>&1 || return 1
  hciconfig -a 2>/dev/null | grep -q 'BD Address: 00:00:00:00:00:00' && return 1
  bluetoothctl show 2>/dev/null | grep -q 'No default controller available' && return 1
  return 0
}

prepare_bluetooth_controller() {
  local fix_args=()

  if [ "$SKIP_BLUETOOTH_FIX" = "1" ]; then
    log "Skipping Bluetooth fix."
    bluetoothctl power on >/dev/null 2>&1 || true
    return 0
  fi

  if [ -x "$FIX_SCRIPT" ]; then
    while IFS= read -r -d '' arg; do
      fix_args+=("$arg")
    done < <(bluetooth_fix_args)

    log "Running MT7925 Bluetooth recovery via $FIX_SCRIPT."
    run_privileged "$FIX_SCRIPT" "${fix_args[@]}" || return 1
  else
    log "No Bluetooth fix script found at $FIX_SCRIPT; trying bluetoothctl power on."
    bluetoothctl power on >/dev/null 2>&1 || true
  fi

  if bluetooth_controller_usable; then
    log "Bluetooth controller looks usable."
    return 0
  fi

  log "Bluetooth controller is still not usable."
  bluetoothctl show 2>&1 || true
  return 1
}

strip_ansi() {
  sed -r 's/\x1B\[[0-9;]*[mK]//g; s/\x01//g; s/\x02//g'
}

scan_with_pyparrot() {
  log "Scanning Swing with pyparrot..."
  run_privileged "$PYTHON_BIN" -m pyparrot.scripts.findMinidrone 2>&1 || true
}

scan_with_bluetoothctl() {
  log "Scanning Swing with bluetoothctl for 20 seconds..."
  timeout 20 bluetoothctl scan on 2>&1 || true
  bluetoothctl scan off >/dev/null 2>&1 || true
}

extract_swing_addr() {
  awk '
    /FOUND A SWING/ { found = 1; next }
    found && /Device/ { print $2; exit }
    /Device [0-9A-Fa-f:]+ .*Swing/ { print $2; exit }
  '
}

find_swing_addr() {
  local scan_output

  scan_output="$(
    {
      scan_with_pyparrot
      scan_with_bluetoothctl
    } | strip_ansi
  )"
  printf '%s\n' "$scan_output" >&2
  printf '%s\n' "$scan_output" | extract_swing_addr | head -n 1
}

find_swing_addr_with_recovery() {
  local swing_addr

  swing_addr="$(find_swing_addr || true)"
  if [ -n "$swing_addr" ]; then
    printf '%s\n' "$swing_addr"
    return 0
  fi

  if [ "$RETRY_BLUETOOTH_RECOVERY" != "1" ] || [ "$SKIP_BLUETOOTH_FIX" = "1" ]; then
    return 1
  fi

  log "Swing scan found no device; rerunning Bluetooth recovery once, then rescanning."
  prepare_bluetooth_controller || return 1
  swing_addr="$(find_swing_addr || true)"
  [ -n "$swing_addr" ] || return 1
  printf '%s\n' "$swing_addr"
}
