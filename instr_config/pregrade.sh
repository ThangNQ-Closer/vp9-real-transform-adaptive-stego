#!/bin/bash
homedir=$1
destdir=$2
cd "$homedir/$destdir" || exit 0
mkdir -p .local/result
script_dir="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
    python3 "$script_dir/check_lab3.py" "$homedir/$destdir" > .local/result/vp9_real_transform_checkwork.txt 2>&1
else
    for c in input_video_ready libvpx_built cover_encoded stego_encoded receiver_verified labtainer_outputs_ready; do
        echo "N - $c"
    done > .local/result/vp9_real_transform_checkwork.txt
fi
