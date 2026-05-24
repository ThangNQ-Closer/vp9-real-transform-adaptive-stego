#!/usr/bin/env python3
import argparse
import json

def main():
    p = argparse.ArgumentParser(description="Print concise verification metrics.")
    p.add_argument("--report", default="verify_report.json")
    args = p.parse_args()
    with open(args.report, "r") as f:
        r = json.load(f)
    for k in ["success", "psnr", "ssim", "embedded_bits", "modified_coeffs", "dc_modified", "zero_to_nonzero", "nonzero_to_zero"]:
        print("%s: %s" % (k, r.get(k)))

if __name__ == "__main__":
    main()
