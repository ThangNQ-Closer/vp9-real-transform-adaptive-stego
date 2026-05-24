Receiver workflow:
  python3 inspect_video.py /shared/stego.ivf
  python3 verify_stego.py --cover /shared/cover.ivf --stego /shared/stego.ivf --embed-log /shared/embed_log.json --output verify_report.json
  python3 extract_metrics.py --report verify_report.json

verify_stego.py decodes both VP9 bitstreams with ffmpeg, calculates PSNR
and SSIM when scikit-image is available, and validates the embed log.
