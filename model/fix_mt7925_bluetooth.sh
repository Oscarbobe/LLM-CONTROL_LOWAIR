#!/usr/bin/env bash
set -u -o pipefail

DEVICE_ID="0489:e111"
UPDATE_FIRMWARE=0
INSTALL_PERSISTENT=0
FIRMWARE_URL="https://gitlab.com/kernel-firmware/linux-firmware/-/raw/main/mediatek/mt7925/BT_RAM_CODE_MT7925_1_1_hdr.bin"
FIRMWARE_TARGET="/lib/firmware/mediatek/mt7925/BT_RAM_CODE_MT7925_1_1_hdr.bin"
LOG_FILE="/tmp/mt7925_bluetooth_fix.log"
ORIGINAL_ARGS=("$@")

usage() {
  cat <<'EOF'
Usage:
  ./fix_mt7925_bluetooth.sh [options]

Options:
  --device VID:PID       USB Bluetooth device id. Default: 0489:e111
  --update-firmware      Download and install latest MT7925 Bluetooth firmware
  --install-persistent   Install a systemd service that runs this fix at boot
  --firmware-url URL     Override firmware download URL
  -h, --help             Show this help

Examples:
  sudo ./fix_mt7925_bluetooth.sh
  sudo ./fix_mt7925_bluetooth.sh --update-firmware
  sudo ./fix_mt7925_bluetooth.sh --install-persistent

What this script does:
  1. Checks for the target USB Bluetooth device.
  2. Adds the VID:PID to btusb if needed.
  3. Disables USB autosuspend for that device.
  4. Restarts/reloads Bluetooth kernel modules and bluetooth.service.
  5. Verifies whether hci0/hci1 becomes usable.

Firmware replacement is only done with --update-firmware.
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

run() {
  log "+ $*"
  "$@"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

die() {
  log "ERROR: $*"
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --device)
      [ "$#" -ge 2 ] || die "--device requires VID:PID"
      DEVICE_ID="$2"
      shift 2
      ;;
    --update-firmware)
      UPDATE_FIRMWARE=1
      shift
      ;;
    --install-persistent)
      INSTALL_PERSISTENT=1
      shift
      ;;
    --firmware-url)
      [ "$#" -ge 2 ] || die "--firmware-url requires URL"
      FIRMWARE_URL="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  if have_cmd sudo; then
    exec sudo "$0" "${ORIGINAL_ARGS[@]}"
  fi
  die "Run as root."
fi

exec > >(tee -a "$LOG_FILE") 2>&1

VID="${DEVICE_ID%%:*}"
PID="${DEVICE_ID##*:}"
VID_LOWER="$(printf '%s' "$VID" | tr 'A-F' 'a-f')"
PID_LOWER="$(printf '%s' "$PID" | tr 'A-F' 'a-f')"
VID_UPPER="$(printf '%s' "$VID" | tr 'a-f' 'A-F')"
PID_UPPER="$(printf '%s' "$PID" | tr 'a-f' 'A-F')"

find_usb_devices() {
  for dev in /sys/bus/usb/devices/*; do
    [ -f "$dev/idVendor" ] || continue
    [ -f "$dev/idProduct" ] || continue
    cur_vid="$(cat "$dev/idVendor")"
    cur_pid="$(cat "$dev/idProduct")"
    if [ "$cur_vid" = "$VID_LOWER" ] && [ "$cur_pid" = "$PID_LOWER" ]; then
      printf '%s\n' "$dev"
    fi
  done
}

show_status() {
  log "Current USB Bluetooth status:"
  lsusb | grep -i "${VID}:${PID}" || true
  lsusb -t || true

  log "Current HCI status:"
  hciconfig -a || true
  bluetoothctl list || true
  bluetoothctl show || true
}

install_firmware() {
  log "Firmware update requested."
  mkdir -p "$(dirname "$FIRMWARE_TARGET")"

  tmp_file="$(mktemp /tmp/mt7925_bt_fw.XXXXXX)"
  if have_cmd curl; then
    run curl -fL "$FIRMWARE_URL" -o "$tmp_file"
  elif have_cmd wget; then
    run wget -O "$tmp_file" "$FIRMWARE_URL"
  else
    rm -f "$tmp_file"
    die "Need curl or wget to download firmware."
  fi

  if [ ! -s "$tmp_file" ]; then
    rm -f "$tmp_file"
    die "Downloaded firmware is empty."
  fi

  if [ -f "$FIRMWARE_TARGET" ]; then
    backup="${FIRMWARE_TARGET}.bak.$(date '+%Y%m%d-%H%M%S')"
    run cp -a "$FIRMWARE_TARGET" "$backup"
    log "Backed up existing firmware to $backup"
  fi

  run install -m 0644 "$tmp_file" "$FIRMWARE_TARGET"
  rm -f "$tmp_file"

  if have_cmd update-initramfs; then
    run update-initramfs -u || true
  fi
}

bind_btusb() {
  if [ ! -d /sys/bus/usb/drivers/btusb ]; then
    run modprobe btusb || die "Cannot load btusb."
  fi

  log "Adding device id ${VID_UPPER}:${PID_UPPER} to btusb."
  printf '%s %s\n' "$VID_UPPER" "$PID_UPPER" > /sys/bus/usb/drivers/btusb/new_id 2>/dev/null || true

  devices="$(find_usb_devices)"
  [ -n "$devices" ] || die "USB device $DEVICE_ID was not found. Plug/replug the Bluetooth adapter and retry."

  printf '%s\n' "$devices" | while IFS= read -r dev; do
    log "Found target USB device: $dev"
    if [ -f "$dev/power/control" ]; then
      log "Disabling autosuspend for $dev"
      printf 'on\n' > "$dev/power/control" 2>/dev/null || true
    fi

    for iface in "$dev":*; do
      [ -e "$iface" ] || continue
      [ -f "$iface/bInterfaceClass" ] || continue
      cls="$(cat "$iface/bInterfaceClass")"
      sub="$(cat "$iface/bInterfaceSubClass")"
      proto="$(cat "$iface/bInterfaceProtocol")"

      if [ "$cls" = "e0" ] && [ "$sub" = "01" ] && [ "$proto" = "01" ]; then
        if [ -L "$iface/driver" ]; then
          log "$iface is already bound to $(basename "$(readlink -f "$iface/driver")")."
        else
          iface_name="$(basename "$iface")"
          log "Binding $iface_name to btusb."
          printf '%s\n' "$iface_name" > /sys/bus/usb/drivers/btusb/bind 2>/dev/null || true
        fi
      fi
    done
  done
}

reset_stack() {
  log "Stopping bluetooth.service."
  run systemctl stop bluetooth || true

  log "Reloading Bluetooth USB modules."
  run modprobe -r btusb btmtk || true
  sleep 1
  run modprobe btusb || die "Cannot reload btusb."

  bind_btusb

  log "Unblocking Bluetooth rfkill."
  run rfkill unblock bluetooth || true

  log "Starting bluetooth.service."
  run systemctl start bluetooth || true
  sleep 2
}

power_on_hci() {
  for hci in /sys/class/bluetooth/hci*; do
    [ -e "$hci" ] || continue
    name="$(basename "$hci")"
    log "Trying to bring up $name."
    run hciconfig "$name" up || true
  done

  if have_cmd btmgmt; then
    run btmgmt power on || true
  fi
}

detect_success() {
  if ! ls /sys/class/bluetooth/hci* >/dev/null 2>&1; then
    log "No HCI controller is registered."
    return 1
  fi

  if hciconfig -a | grep -q 'BD Address: 00:00:00:00:00:00'; then
    log "HCI controller exists but still has zero BD Address."
    return 1
  fi

  if bluetoothctl show 2>/dev/null | grep -q 'No default controller available'; then
    log "BlueZ still reports no default controller."
    return 1
  fi

  return 0
}

install_persistent_service() {
  target_script="/usr/local/sbin/fix-mt7925-bluetooth.sh"
  service_file="/etc/systemd/system/fix-mt7925-bluetooth.service"

  log "Installing persistent systemd fix."
  run install -m 0755 "$0" "$target_script"

  cat > "$service_file" <<EOF
[Unit]
Description=Fix MediaTek MT7925 Bluetooth btusb binding
After=systemd-modules-load.service
Before=bluetooth.service

[Service]
Type=oneshot
ExecStart=$target_script --device $DEVICE_ID
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

  run systemctl daemon-reload
  run systemctl enable fix-mt7925-bluetooth.service
  log "Persistent service installed: $service_file"
  log "It will run automatically at boot. You can also run it manually with:"
  log "  sudo systemctl start fix-mt7925-bluetooth.service"
}

main() {
  log "MT7925 Bluetooth fix started. Log: $LOG_FILE"
  log "Target USB device: $DEVICE_ID"

  show_status

  if [ "$UPDATE_FIRMWARE" -eq 1 ]; then
    install_firmware
  else
    log "Skipping firmware replacement. Use --update-firmware to install latest MT7925 BT firmware."
  fi

  reset_stack
  power_on_hci
  show_status

  if detect_success; then
    log "Bluetooth controller looks usable."
    if [ "$INSTALL_PERSISTENT" -eq 1 ]; then
      install_persistent_service
    fi
    log "Next: run the local Swing automation:"
    log "  cd /home/abc/桌面/LLM-CONTROL_LOWAIR"
    log "  ./model/run_swing_direct_flight.sh"
    exit 0
  fi

  log "Bluetooth is still not usable."
  log "Recent kernel messages:"
  dmesg -T | grep -Ei 'bluetooth|btusb|btmtk|firmware|0489|e111|mt79|hci' | tail -80 || true
  log "If you still see 'Failed to set up firmware (-110)', retry once with:"
  log "  sudo ./fix_mt7925_bluetooth.sh --update-firmware"
  log "If it still fails after firmware update and reboot, use an external Linux-compatible USB Bluetooth adapter."
  exit 2
}

main
