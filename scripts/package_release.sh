#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="${1:-$(date +%Y%m%d_%H%M%S)}"
PACKAGE_NAME="LLM-CONTROL_LOWAIR-${VERSION}"
DIST_DIR="$ROOT_DIR/dist"
STAGING_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

mkdir -p "$DIST_DIR"

if ! command -v rsync >/dev/null 2>&1; then
  echo "ERROR: rsync 未安装，无法安全生成发布包。请先安装 rsync。"
  exit 1
fi

rsync -a ./ "$STAGING_DIR/$PACKAGE_NAME/" \
  --exclude ".git/" \
  --exclude ".agents/" \
  --exclude ".codex/" \
  --exclude ".omo/" \
  --exclude "__pycache__/" \
  --exclude ".pytest_cache/" \
  --exclude ".mypy_cache/" \
  --exclude ".ruff_cache/" \
  --exclude "dist/" \
  --exclude "*.zip" \
  --exclude "*.tar.gz" \
  --exclude "data/logs/*.jsonl" \
  --exclude "data/raw/audio/*.wav" \
  --exclude "data/raw/audio/*.txt" \
  --exclude "data/reports/*.md" \
  --exclude "data/simulation/" \
  --exclude "*.asv" \
  --exclude "*.slxc" \
  --exclude "*.autosave" \
  --exclude "slprj/"

if command -v zip >/dev/null 2>&1; then
  (cd "$STAGING_DIR" && zip -qr "$DIST_DIR/$PACKAGE_NAME.zip" "$PACKAGE_NAME")
  echo "发布包已生成：$DIST_DIR/$PACKAGE_NAME.zip"
else
  tar -C "$STAGING_DIR" -czf "$DIST_DIR/$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
  echo "未检测到 zip，已生成 tar.gz：$DIST_DIR/$PACKAGE_NAME.tar.gz"
fi
