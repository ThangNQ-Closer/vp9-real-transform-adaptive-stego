#!/bin/bash
set -euo pipefail
if [ $# -lt 2 ]; then
  echo "Usage: $0 /path/to/input_video.mp4 /path/to/vp9-real-transform-adaptive-stego-with-video.tar" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO="$1"
OUT="$2"
if [ ! -s "$VIDEO" ]; then
  echo "Input video not found or empty: $VIDEO" >&2
  exit 1
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
LAB="vp9-real-transform-adaptive-stego"
mkdir -p "$TMP/$LAB"
rsync -a --exclude='.git/' --exclude='imodule/' --exclude='sender/libvpx/' --exclude='**/home_tar/' --exclude='**/sys_tar/' --exclude='**/*.tar.gz' --exclude='*.lab' "$ROOT/" "$TMP/$LAB/"
cp "$VIDEO" "$TMP/$LAB/sender/input_video.mp4"
if ! grep -qx 'input_video.mp4' "$TMP/$LAB/config/sender-home_tar.list"; then
  printf '\ninput_video.mp4\n' >> "$TMP/$LAB/config/sender-home_tar.list"
fi
mkdir -p "$(dirname "$OUT")"
tar -cf "$OUT" -C "$TMP" "$LAB"
echo "Created private video imodule: $OUT"
echo "Install with: imodule file://$OUT"
echo "Then rebuild local images with: cd ~/labtainer/trunk/labs/$LAB && ./scripts/build_local_images.sh"
