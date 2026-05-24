#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

try:
    from skimage.metrics import structural_similarity as skimage_ssim
except Exception:
    try:
        from skimage.measure import compare_ssim as skimage_ssim
    except Exception:
        skimage_ssim = None

def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError(err.decode("utf-8", "replace"))
    return out.decode("utf-8", "replace")

def ffprobe_dims(path):
    out = run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", path
    ])
    data = json.loads(out)
    st = data.get("streams", [{}])[0]
    return int(st.get("width", 0)), int(st.get("height", 0))

def decode_raw(path, out_path):
    run(["ffmpeg", "-y", "-v", "error", "-i", path, "-pix_fmt", "yuv420p", "-f", "rawvideo", out_path])
    return os.path.exists(out_path) and os.path.getsize(out_path) > 0

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def metrics(cover_raw, stego_raw, width, height):
    with open(cover_raw, "rb") as f:
        a = np.frombuffer(f.read(), dtype=np.uint8)
    with open(stego_raw, "rb") as f:
        b = np.frombuffer(f.read(), dtype=np.uint8)
    n = min(a.size, b.size)
    if n == 0:
        return None, None
    a = a[:n].astype(np.float64)
    b = b[:n].astype(np.float64)
    mse = np.mean((a - b) ** 2)
    psnr = 99.0 if mse == 0 else 20.0 * math.log10(255.0 / math.sqrt(mse))
    ssim = None
    frame_size = int(width * height * 3 / 2)
    if skimage_ssim is not None and frame_size > 0 and n >= frame_size:
        frames = int(n / frame_size)
        vals = []
        with open(cover_raw, "rb") as fa, open(stego_raw, "rb") as fb:
            for _ in range(frames):
                ya = np.frombuffer(fa.read(width * height), dtype=np.uint8).reshape((height, width))
                yb = np.frombuffer(fb.read(width * height), dtype=np.uint8).reshape((height, width))
                fa.seek(frame_size - width * height, 1)
                fb.seek(frame_size - width * height, 1)
                vals.append(float(skimage_ssim(ya, yb, data_range=255)))
        if vals:
            ssim = float(sum(vals) / len(vals))
    return float(psnr), ssim

def main():
    p = argparse.ArgumentParser(description="Verify real VP9 stego decode, PSNR/SSIM, and embed invariants.")
    p.add_argument("--cover", required=True)
    p.add_argument("--stego", required=True)
    p.add_argument("--embed-log", required=True)
    p.add_argument("--output", default="verify_report.json")
    args = p.parse_args()
    tmp = tempfile.mkdtemp(prefix="vp9verify_")
    report = {
        "cover_exists": os.path.exists(args.cover),
        "stego_exists": os.path.exists(args.stego),
        "decode_cover_ok": False,
        "decode_stego_ok": False,
        "psnr": None,
        "ssim": None,
        "embedded_bits": 0,
        "modified_coeffs": 0,
        "dc_modified": None,
        "zero_to_nonzero": None,
        "nonzero_to_zero": None,
        "cover_stego_different": False,
        "success": False
    }
    try:
        if report["cover_exists"] and report["stego_exists"]:
            width, height = ffprobe_dims(args.cover)
            cover_raw = os.path.join(tmp, "cover.yuv")
            stego_raw = os.path.join(tmp, "stego.yuv")
            report["decode_cover_ok"] = decode_raw(args.cover, cover_raw)
            report["decode_stego_ok"] = decode_raw(args.stego, stego_raw)
            if report["decode_cover_ok"] and report["decode_stego_ok"]:
                psnr, ssim = metrics(cover_raw, stego_raw, width, height)
                report["psnr"] = psnr
                report["ssim"] = ssim
            report["cover_stego_different"] = sha256(args.cover) != sha256(args.stego)
        if os.path.exists(args.embed_log):
            with open(args.embed_log, "r") as f:
                emb = json.load(f)
            for k in ["embedded_bits", "modified_coeffs", "dc_modified", "zero_to_nonzero", "nonzero_to_zero"]:
                report[k] = emb.get(k)
        psnr_ok = report["psnr"] is not None and report["psnr"] >= 10.0 and report["psnr"] <= 100.0
        ssim_ok = report["ssim"] is None or (report["ssim"] >= 0.0 and report["ssim"] <= 1.0)
        report["success"] = bool(
            report["cover_exists"] and report["stego_exists"] and
            report["decode_cover_ok"] and report["decode_stego_ok"] and
            psnr_ok and ssim_ok and
            report["embedded_bits"] and report["embedded_bits"] > 0 and
            report["modified_coeffs"] and report["modified_coeffs"] > 0 and
            report["dc_modified"] == 0 and
            report["zero_to_nonzero"] == 0 and
            report["nonzero_to_zero"] == 0 and
            report["cover_stego_different"]
        )
    finally:
        shutil.rmtree(tmp)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["success"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
