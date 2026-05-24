Sender workflow:
  ./view_input_video.sh --serve
  python3 prepare_input.py
  ./build_libvpx.sh
  python3 patch_libvpx.py
  ./build_libvpx.sh
  ./encode_cover.sh
  ./encode_logonly.sh
  ./encode_stego.sh
  python3 inspect_embed_log.py --input embed_log.json

Payload used by the lab:
  KHOA ATTT PTIT

Video viewing:
  Run ./view_input_video.sh --serve in the sender container, then open the URL
  printed by the script in Firefox on the Ubuntu VM desktop. This avoids ffplay
  GUI errors inside Docker containers.

The patch uses VP9_STEGO_MODE=off|log|embed and edits quantized transform
coefficients in libvpx VP9 tokenization after quantization and before entropy
token emission. It is intentionally defensive and forensic-oriented.
