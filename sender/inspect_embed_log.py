#!/usr/bin/env python3
import argparse
import json
import sys

def main():
    p = argparse.ArgumentParser(description="Inspect real VP9 qcoeff stego embed log.")
    p.add_argument("--input", default="embed_log.json")
    args = p.parse_args()
    with open(args.input, "r") as f:
        log = json.load(f)
    fields = [
        "payload", "payload_bits", "embedded_bits", "modified_coeffs",
        "skipped_zero", "skipped_dc", "skipped_small",
        "skipped_parity_already_match", "zero_to_nonzero",
        "nonzero_to_zero", "dc_modified"
    ]
    for name in fields:
        print("%s: %s" % (name, log.get(name)))
    entries = log.get("entries", [])
    print("entries: %d" % len(entries))
    for e in entries[:10]:
        print("seq=%s plane=%s block=%s c=%s old=%s new=%s bit=%s" % (
            e.get("sequence_id"), e.get("plane"), e.get("block"),
            e.get("coeff_index"), e.get("old_coeff"), e.get("new_coeff"),
            e.get("embedded_bit")))
    ok = (
        log.get("embedded_bits", 0) > 0 and
        log.get("modified_coeffs", 0) > 0 and
        log.get("dc_modified", 1) == 0 and
        log.get("zero_to_nonzero", 1) == 0 and
        log.get("nonzero_to_zero", 1) == 0
    )
    if not ok:
        sys.exit("embed log failed invariant checks")

if __name__ == "__main__":
    main()
