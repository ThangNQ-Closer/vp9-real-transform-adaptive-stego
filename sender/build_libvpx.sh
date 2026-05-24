#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ ! -d libvpx ]; then
    echo "[build] libvpx source not found, cloning official repository"
    git clone https://chromium.googlesource.com/webm/libvpx libvpx
else
    echo "[build] using existing ./libvpx source"
fi
cd libvpx
if [ ! -x ./configure ]; then
    echo "libvpx configure script not found" >&2
    exit 1
fi
if [ ! -f Makefile ]; then
    ./configure \
        --disable-unit-tests \
        --disable-docs \
        --enable-vp9 \
        --enable-vp8
fi
jobs=2
if command -v nproc >/dev/null 2>&1; then jobs="$(nproc)"; fi
make -j"$jobs"
make -j"$jobs" vpxenc vpxdec
if [ -x ./vpxenc ]; then
    ./vpxenc --help >/dev/null 2>&1 || true
    echo "[build] vpxenc ready at $(pwd)/vpxenc"
elif [ -x ./vpxenc_g ]; then
    echo "[build] vpxenc_g ready at $(pwd)/vpxenc_g"
else
    echo "vpxenc was not built" >&2
    exit 1
fi
