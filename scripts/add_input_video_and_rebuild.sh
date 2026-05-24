#!/bin/bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 /path/to/input_video.mp4" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$1"
if [ ! -s "$SRC" ]; then
  echo "Input video not found or empty: $SRC" >&2
  exit 1
fi
cp "$SRC" "$ROOT/sender/input_video.mp4"
if ! grep -qx 'input_video.mp4' "$ROOT/config/sender-home_tar.list"; then
  printf '\ninput_video.mp4\n' >> "$ROOT/config/sender-home_tar.list"
fi
"$ROOT/scripts/build_local_images.sh"
echo "Installed sender/input_video.mp4 and rebuilt local Labtainer images."
