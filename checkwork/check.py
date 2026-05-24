#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile

CHECKS = [
    "input_video_ready",
    "libvpx_built",
    "cover_encoded",
    "stego_encoded",
    "receiver_verified",
    "labtainer_outputs_ready"
]

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def candidate_dirs(base):
    out = []
    for d in [base, os.getcwd(), os.path.expanduser("~"), "/shared"]:
        for x in [d, os.path.join(d, "sender"), os.path.join(d, "receiver"), os.path.join(d, "shared"), os.path.join(d, ".local", "result")]:
            if x not in out:
                out.append(x)
    return out

def find_file(base, name):
    for d in candidate_dirs(base):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    for root in [base, os.path.expanduser("~"), "/shared"]:
        if not os.path.isdir(root):
            continue
        for cur, dirs, files in os.walk(root):
            if name in files:
                return os.path.join(cur, name)
            if cur[len(root):].count(os.sep) >= 4:
                dirs[:] = []
    return None

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def decodes(path):
    if not path or not os.path.exists(path) or os.path.getsize(path) <= 0:
        return False
    try:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()
        return p.returncode == 0
    except Exception:
        return False

def lab_archive_small(base):
    # Do not require a .lab during live checkwork, but reject one that carries bulky media/build output.
    bad_suffix = (".mp4", ".y4m", ".ivf", ".webm", ".o", ".a")
    for root, dirs, files in os.walk(base):
        if "libvpx" in root.split(os.sep):
            continue
        for name in files:
            p = os.path.join(root, name)
            low = name.lower()
            if low.endswith(".lab"):
                if os.path.getsize(p) > 1024 * 1024:
                    return False
                try:
                    z = zipfile.ZipFile(p)
                    for item in z.namelist():
                        if item.lower().endswith(bad_suffix):
                            return False
                except Exception:
                    pass
    return True

def evaluate(base):
    paths = {
        "input": find_file(base, "input_video.mp4"),
        "cover_y4m": find_file(base, "cover.y4m"),
        "vpxenc": find_file(base, "vpxenc"),
        "cover": find_file(base, "cover.ivf"),
        "stego": find_file(base, "stego.ivf"),
        "embed": find_file(base, "embed_log.json"),
        "coeff": find_file(base, "coeff_log.json"),
        "verify": find_file(base, "verify_report.json")
    }
    res = dict((c, False) for c in CHECKS)
    res["input_video_ready"] = bool(paths["cover_y4m"] and os.path.getsize(paths["cover_y4m"]) > 0)
    res["libvpx_built"] = bool(paths["vpxenc"] and os.path.getsize(paths["vpxenc"]) > 0)
    res["cover_encoded"] = bool(paths["cover"] and decodes(paths["cover"]))
    emb = {}
    if paths["embed"]:
        try:
            emb = load_json(paths["embed"])
        except Exception:
            emb = {}
    coeff_ok = True
    if paths["coeff"]:
        try:
            c = load_json(paths["coeff"])
            coeff_ok = c.get("total_coeff_seen", 0) > 0 and c.get("nonzero_coeff_seen", 0) > 0 and c.get("eligible_coeff_seen", 0) > 0 and len(c.get("sample_entries", [])) > 0
        except Exception:
            coeff_ok = False
    stego_diff = bool(paths["cover"] and paths["stego"] and sha256(paths["cover"]) != sha256(paths["stego"]))
    res["stego_encoded"] = bool(
        paths["stego"] and decodes(paths["stego"]) and stego_diff and
        emb.get("embedded_bits", 0) > 0 and emb.get("modified_coeffs", 0) > 0 and
        emb.get("dc_modified") == 0 and emb.get("zero_to_nonzero") == 0 and emb.get("nonzero_to_zero") == 0 and
        coeff_ok
    )
    if paths["verify"]:
        try:
            v = load_json(paths["verify"])
        except Exception:
            v = {}
        psnr = v.get("psnr")
        ssim = v.get("ssim")
        psnr_ok = isinstance(psnr, (int, float)) and psnr >= 10.0 and psnr <= 100.0
        ssim_ok = ssim is None or (isinstance(ssim, (int, float)) and ssim >= 0.0 and ssim <= 1.0)
        res["receiver_verified"] = bool(
            v.get("success") and v.get("decode_cover_ok") and v.get("decode_stego_ok") and
            psnr_ok and ssim_ok and v.get("cover_stego_different") and
            v.get("embedded_bits", 0) > 0 and v.get("modified_coeffs", 0) > 0 and
            v.get("dc_modified") == 0 and v.get("zero_to_nonzero") == 0 and v.get("nonzero_to_zero") == 0
        )
    res["labtainer_outputs_ready"] = all(res[c] for c in CHECKS[:-1]) and lab_archive_small(base)
    return res

def main():
    p = argparse.ArgumentParser(description="Check VP9 real transform adaptive stego lab artifacts.")
    p.add_argument("--base", default=os.getcwd())
    args = p.parse_args()
    r = evaluate(args.base)
    for c in CHECKS:
        print(("Y" if r.get(c) else "N") + " - " + c)
    if not all(r.get(c) for c in CHECKS):
        sys.exit(1)

if __name__ == "__main__":
    main()
