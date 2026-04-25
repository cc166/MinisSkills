#!/bin/sh
set -eu

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEST_DIR=${1:-/var/minis/skills/codex-image}
BIN_DIR=${BIN_DIR:-/usr/local/bin}

mkdir -p "$DEST_DIR" "$BIN_DIR"
rm -rf "$DEST_DIR"
mkdir -p "$DEST_DIR"

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$SRC_DIR/" "$DEST_DIR/"
else
  cp -R "$SRC_DIR"/. "$DEST_DIR"/
  find "$DEST_DIR" -type d -name '.git' -prune -exec rm -rf {} + 2>/dev/null || true
  find "$DEST_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
  find "$DEST_DIR" -type f -name '*.pyc' -delete 2>/dev/null || true
fi

if [ -f "$DEST_DIR/bin/image2" ]; then
  cp "$DEST_DIR/bin/image2" "$BIN_DIR/image2"
  chmod +x "$BIN_DIR/image2"
fi

chmod +x "$DEST_DIR"/scripts/*.py "$DEST_DIR"/bin/* 2>/dev/null || true
printf 'installed codex-image from %s to %s\n' "$SRC_DIR" "$DEST_DIR"
