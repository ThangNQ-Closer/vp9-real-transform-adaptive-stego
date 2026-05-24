#!/usr/bin/env python3
import argparse
import json
import subprocess

def main():
    p = argparse.ArgumentParser(description="Inspect VP9 video stream metadata with ffprobe.")
    p.add_argument("video")
    args = p.parse_args()
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", args.video
    ])
    print(json.dumps(json.loads(out.decode("utf-8")), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
