#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
find_vpxenc() {
    for p in ./libvpx/vpxenc ./libvpx/vpxenc_g ./vpxenc; do
        if [ -x "$p" ]; then echo "$p"; return 0; fi
    done
    return 1
}

ensure_cover_y4m() {
    if [ ! -s cover.y4m ]; then
        echo "cover.y4m not found; running python3 prepare_input.py first"
        python3 prepare_input.py
    fi
}

ensure_vpxenc() {
    local enc
    if enc="$(find_vpxenc)"; then
        echo "$enc"
        return 0
    fi
    echo "vpxenc not found; running ./build_libvpx.sh first" >&2
    ./build_libvpx.sh >&2
    if enc="$(find_vpxenc)"; then
        echo "$enc"
        return 0
    fi
    echo "vpxenc was not created by build_libvpx.sh" >&2
    return 1
}

ensure_patched_vpxenc() {
    local enc
    enc="$(ensure_vpxenc)"
    if [ -d libvpx ] && ! grep -q "VP9_STEGO_PATCH_BEGIN" libvpx/vp9/encoder/vp9_tokenize.c 2>/dev/null; then
        echo "libvpx source is not patched yet; running python3 patch_libvpx.py" >&2
        python3 patch_libvpx.py >&2
        echo "Patch applied. Rebuilding vpxenc so VP9_STEGO_MODE can affect qcoeff." >&2
        ./build_libvpx.sh >&2
        enc="$(ensure_vpxenc)"
    fi
    echo "$enc"
}

ensure_cover_y4m
enc="$(ensure_vpxenc)"
VP9_STEGO_MODE=off "$enc" --codec=vp9 --ivf --good --cpu-used=4 --threads=1 -o cover.ivf cover.y4m
test -s cover.ivf
mkdir -p /shared 2>/dev/null || true
cp cover.ivf /shared/ 2>/dev/null || true
echo "wrote cover.ivf"
