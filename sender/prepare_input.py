#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

def run(cmd):
    print("+ " + " ".join(cmd))
    return subprocess.check_call(cmd)

def main():
    p = argparse.ArgumentParser(description="Prepare a short Y4M cover video for real VP9 encoding.")
    p.add_argument("--input", default="input_video.mp4")
    p.add_argument("--output", default="cover.y4m")
    args = p.parse_args()
    if os.path.exists(args.input):
        cmd = [
            "ffmpeg", "-y", "-i", args.input, "-t", "5",
            "-vf", "scale=320:-2,fps=15", "-pix_fmt", "yuv420p", args.output
        ]
    else:
        print("input_video.mp4 not found; generating deterministic ffmpeg testsrc2 fallback")
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
            "-t", "5", "-pix_fmt", "yuv420p", args.output
        ]
    run(cmd)
    if not os.path.exists(args.output) or os.path.getsize(args.output) <= 0:
        sys.exit("failed to create " + args.output)
    print("created %s (%d bytes)" % (args.output, os.path.getsize(args.output)))

if __name__ == "__main__":
    main()
